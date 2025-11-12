<script setup lang="ts">
import { ref, computed, watch, onBeforeUnmount } from 'vue'
import { CheckIcon, ChevronsUpDownIcon, LoaderIcon } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { api } from '@/services/axios'
import { cn } from '@/lib/utils'

interface Entity {
  id: string
  label: string
  sublabel?: string
  secondary?: string
}

const props = defineProps<{
  scope: 'device' | 'user'
}>()

const model = defineModel<string | null>({ default: null })

const open = ref(false)
const search = ref('')
const entities = ref<Entity[]>([])
const loading = ref(false)
const loading_more = ref(false)
const total_count = ref(0)
const current_offset = ref(0)
const LIMIT = 50

// Infinite scroll refs
const sentinel_ref = ref<HTMLElement | null>(null)
let observer: IntersectionObserver | null = null

function parse_user_agent(ua: string | null): string | null {
  if (!ua) return null

  // Extract browser
  let browser = 'Unknown'
  if (ua.includes('Chrome') && !ua.includes('Edg')) browser = 'Chrome'
  else if (ua.includes('Safari') && !ua.includes('Chrome')) browser = 'Safari'
  else if (ua.includes('Firefox')) browser = 'Firefox'
  else if (ua.includes('Edg')) browser = 'Edge'
  else if (ua.includes('Opera') || ua.includes('OPR')) browser = 'Opera'

  // Extract OS
  let os = ''
  if (ua.includes('Mac OS')) os = 'Mac'
  else if (ua.includes('Windows')) os = 'Windows'
  else if (ua.includes('Linux')) os = 'Linux'
  else if (ua.includes('Android')) os = 'Android'
  else if (ua.includes('iPhone') || ua.includes('iPad')) os = 'iOS'

  return os ? `${browser} on ${os}` : browser
}

const selected_entity = computed(() => {
  if (!model.value) return null
  return entities.value.find(e => e.id === model.value) || null
})

const placeholder = computed(() => {
  return props.scope === 'device' ? 'All Devices' : 'All Users'
})

const search_placeholder = computed(() => {
  return props.scope === 'device' ? 'Search devices...' : 'Search users...'
})

function map_response_to_entities(data: any): Entity[] {
  if (props.scope === 'device') {
    return data.devices.map((d: any) => ({
      id: d.id,
      label: parse_user_agent(d.user_agent) || d.id.slice(0, 8),
      secondary: d.id.slice(0, 8),
      sublabel: `${d.session_count} sessions`
    }))
  } else {
    return data.users.map((u: any) => ({
      id: u.id,
      label: u.email,
      secondary: u.username || undefined,
      sublabel: `${u.attempt_count} attempts`
    }))
  }
}

async function fetch_entities(search_query?: string) {
  loading.value = true
  current_offset.value = 0
  try {
    const endpoint = props.scope === 'device' ? '/api/admin/devices' : '/api/admin/users'
    const params: Record<string, string | number> = { limit: LIMIT, offset: 0 }
    if (search_query) {
      params.search = search_query
    }

    const response = await api.get(endpoint, { params })
    const data = response.data

    entities.value = map_response_to_entities(data)
    total_count.value = data.total_count
    current_offset.value = LIMIT
  } catch (error) {
    console.error('Failed to fetch entities:', error)
  } finally {
    loading.value = false
  }
}

async function fetch_more_entities() {
  if (loading_more.value || loading.value) return
  if (entities.value.length >= total_count.value) return

  loading_more.value = true
  try {
    const endpoint = props.scope === 'device' ? '/api/admin/devices' : '/api/admin/users'
    const params: Record<string, string | number> = {
      limit: LIMIT,
      offset: current_offset.value
    }
    if (search.value) {
      params.search = search.value
    }

    const response = await api.get(endpoint, { params })
    const data = response.data

    const new_entities = map_response_to_entities(data)
    entities.value = [...entities.value, ...new_entities]
    current_offset.value += LIMIT
  } catch (error) {
    console.error('Failed to fetch more entities:', error)
  } finally {
    loading_more.value = false
  }
}

function select_entity(entity_id: string) {
  model.value = model.value === entity_id ? null : entity_id
  open.value = false
}

function clear_selection() {
  model.value = null
  open.value = false
}

const has_more = computed(() => entities.value.length < total_count.value)

// Setup intersection observer for infinite scroll
function setup_observer() {
  if (observer) {
    observer.disconnect()
  }

  observer = new IntersectionObserver(
    (entries) => {
      if (entries[0].isIntersecting && has_more.value) {
        fetch_more_entities()
      }
    },
    { threshold: 0.1 }
  )

  if (sentinel_ref.value) {
    observer.observe(sentinel_ref.value)
  }
}

function cleanup_observer() {
  if (observer) {
    observer.disconnect()
    observer = null
  }
}

// Watch sentinel ref to setup observer when it becomes available
watch(sentinel_ref, (el) => {
  if (el && open.value) {
    setup_observer()
  }
})

// Debounced search
let search_timeout: ReturnType<typeof setTimeout> | null = null
watch(search, (value) => {
  if (search_timeout) clearTimeout(search_timeout)
  search_timeout = setTimeout(() => {
    fetch_entities(value || undefined)
  }, 300)
})

// Fetch on open and setup observer
watch(open, (is_open) => {
  if (is_open) {
    if (entities.value.length === 0) {
      fetch_entities()
    }
    // Setup observer after a tick to ensure DOM is ready
    setTimeout(setup_observer, 100)
  } else {
    cleanup_observer()
  }
})

// Refetch when scope changes
watch(() => props.scope, () => {
  entities.value = []
  model.value = null
  current_offset.value = 0
  total_count.value = 0
  if (open.value) {
    fetch_entities()
  }
})

onBeforeUnmount(() => {
  cleanup_observer()
})
</script>

<template>
  <Popover v-model:open="open">
    <PopoverTrigger as-child>
      <Button
        variant="outline"
        role="combobox"
        :aria-expanded="open"
        class="w-full md:w-[250px] justify-between"
      >
        <span class="truncate">
          {{ selected_entity?.label || placeholder }}
        </span>
        <ChevronsUpDownIcon class="ml-2 h-4 w-4 shrink-0 opacity-50" />
      </Button>
    </PopoverTrigger>
    <PopoverContent class="w-[300px] p-0">
      <Command>
        <CommandInput v-model="search" :placeholder="search_placeholder" />
        <CommandList>
          <CommandEmpty>
            <span v-if="loading">Loading...</span>
            <span v-else>No results found.</span>
          </CommandEmpty>
          <CommandGroup>
            <!-- Clear selection option -->
            <CommandItem
              value="__clear__"
              @select="clear_selection"
            >
              <CheckIcon
                :class="cn(
                  'mr-2 h-4 w-4',
                  !model ? 'opacity-100' : 'opacity-0',
                )"
              />
              <span class="text-gray-500">{{ placeholder }}</span>
            </CommandItem>

            <!-- Entity options -->
            <CommandItem
              v-for="entity in entities"
              :key="entity.id"
              :value="entity.id"
              @select="() => select_entity(entity.id)"
            >
              <CheckIcon
                :class="cn(
                  'mr-2 h-4 w-4 shrink-0',
                  model === entity.id ? 'opacity-100' : 'opacity-0',
                )"
              />
              <div class="flex flex-col min-w-0">
                <span class="truncate">{{ entity.label }}</span>
                <span v-if="entity.secondary" class="text-xs text-gray-400 truncate">{{ entity.secondary }}</span>
                <span v-if="entity.sublabel" class="text-xs text-gray-500">{{ entity.sublabel }}</span>
              </div>
            </CommandItem>

            <!-- Sentinel for infinite scroll -->
            <div
              v-if="has_more"
              ref="sentinel_ref"
              class="flex items-center justify-center py-2 text-xs text-gray-500"
            >
              <LoaderIcon v-if="loading_more" class="h-4 w-4 animate-spin mr-2" />
              <span v-if="loading_more">Loading more...</span>
              <span v-else>Scroll for more</span>
            </div>
          </CommandGroup>
        </CommandList>
      </Command>
      <div v-if="total_count > 0" class="px-2 py-1 text-xs text-gray-500 border-t">
        Showing {{ entities.length }} of {{ total_count }}
      </div>
    </PopoverContent>
  </Popover>
</template>
