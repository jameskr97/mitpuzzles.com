<script setup lang="ts">
import { ref, shallowRef, onMounted, onBeforeUnmount } from 'vue'
import { basicSetup } from 'codemirror'
import { EditorState } from '@codemirror/state'
import { EditorView, keymap, placeholder } from '@codemirror/view'
import { sql, PostgreSQL } from '@codemirror/lang-sql'
import { autocompletion, type CompletionContext } from '@codemirror/autocomplete'
import Container from '@/core/components/ui/Container.vue'
import { Button } from '@/core/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/core/components/ui/table'
import { useAnalysisStore } from '@/features/analysis/stores/useAnalysisStore'
import { api } from '@/core/services/axios'

const store = useAnalysisStore()

const editor_container = ref<HTMLElement>()
const editor_view = shallowRef<EditorView>()
const preview_data = ref<{ columns: string[]; rows: any[]; total_rows: number } | null>(null)
const loading_preview = ref(false)
const loading_download = ref(false)
const error_message = ref('')

let db_schema: Record<string, string[]> = {}

function schema_completion(context: CompletionContext) {
  const word = context.matchBefore(/\w*/)
  if (!word || (word.from === word.to && !context.explicit)) return null

  const before = context.state.sliceDoc(Math.max(0, word.from - 200), word.from).trimEnd()

  const dot_match = before.match(/(\w+)\.\s*$/)
  if (dot_match) {
    const table = dot_match[1].toLowerCase()
    const cols = db_schema[table]
    if (cols) {
      return {
        from: word.from,
        options: cols.map(col => ({ label: col, type: 'property', detail: table })),
      }
    }
  }

  const tables_only = /\b(?:FROM|JOIN)\s*$/i.test(before)
  if (tables_only) {
    return {
      from: word.from,
      options: Object.keys(db_schema).map(t => ({ label: t, type: 'type', detail: 'table' })),
    }
  }

  const doc = context.state.doc.toString()
  const active_tables = new Set<string>()
  for (const m of doc.matchAll(/\b(?:FROM|JOIN)\s+(\w+)/gi)) {
    const t = m[1].toLowerCase()
    if (db_schema[t]) active_tables.add(t)
  }

  const options: { label: string; type: string; detail: string }[] = []
  if (active_tables.size > 0) {
    for (const table of active_tables) {
      for (const col of db_schema[table]) {
        options.push({ label: col, type: 'property', detail: table })
      }
    }
  } else {
    options.push(...Object.keys(db_schema).map(t => ({ label: t, type: 'type', detail: 'table' })))
  }

  return { from: word.from, options }
}

function get_sql(): string {
  return editor_view.value?.state.doc.toString() ?? ''
}

onMounted(async () => {
  try {
    const response = await api.get('/api/data-export/schema')
    db_schema = response.data
  } catch {
    db_schema = { puzzle: ['id', 'puzzle_type', 'puzzle_size', 'puzzle_difficulty'] }
  }

  const state = EditorState.create({
    doc: 'SELECT * FROM puzzle',
    extensions: [
      basicSetup,
      sql({ dialect: PostgreSQL, upperCaseKeywords: true }),
      autocompletion({ override: [schema_completion] }),
      keymap.of([
        { key: 'Mod-Enter', run: () => { run_preview(); return true } },
      ]),
      placeholder('SELECT * FROM puzzle'),
      EditorView.theme({
        '&': { maxHeight: '400px' },
        '.cm-scroller': { overflow: 'auto' },
      }),
    ],
  })
  editor_view.value = new EditorView({ state, parent: editor_container.value! })
})

onBeforeUnmount(() => {
  editor_view.value?.destroy()
})

function build_request_body() {
  return {
    sql: get_sql(),
    puzzle_types: store.puzzle_types.size > 0 ? [...store.puzzle_types] : null,
    puzzle_sizes: store.puzzle_sizes.size > 0 ? [...store.puzzle_sizes] : null,
    puzzle_difficulties: store.difficulties.size > 0 ? [...store.difficulties] : null,
    filter_user_id: store.scope === 'user' && store.selected_entity_id ? store.selected_entity_id : null,
    filter_device_id: store.scope === 'device' && store.selected_entity_id ? store.selected_entity_id : null,
    solved_filter: store.solved_filter !== 'all' ? store.solved_filter : null,
    date_start: store.date_start || null,
    date_end: store.date_end || null,
  }
}

async function run_preview() {
  loading_preview.value = true
  error_message.value = ''
  preview_data.value = null
  try {
    const response = await api.post('/api/data-export/sql/preview', build_request_body())
    preview_data.value = response.data
  } catch (err: any) {
    error_message.value = err.response?.data?.detail || 'Query failed'
  } finally {
    loading_preview.value = false
  }
}

async function run_download() {
  loading_download.value = true
  error_message.value = ''
  try {
    const response = await api.post('/api/data-export/sql/download', build_request_body(), {
      responseType: 'blob',
    })
    const blob = new Blob([response.data], { type: 'application/vnd.apache.parquet' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'query_result.parquet'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  } catch (err: any) {
    if (err.response?.data instanceof Blob) {
      const text = await err.response.data.text()
      try {
        error_message.value = JSON.parse(text).detail || 'Download failed'
      } catch {
        error_message.value = 'Download failed'
      }
    } else {
      error_message.value = err.response?.data?.detail || 'Download failed'
    }
  } finally {
    loading_download.value = false
  }
}

function truncate(val: any, max = 80): string {
  const s = String(val ?? '')
  return s.length > max ? s.slice(0, max) + '...' : s
}
</script>

<template>
  <div class="grid grid-cols-1 grid-rows-[auto_1fr] h-full gap-2 overflow-hidden">
    <Container>
      <div class="flex flex-col gap-2">
        <label class="text-sm font-medium text-gray-700">
          SQL Query
        </label>
        <p class="text-md text-gray-500">
          The query written below will further filter the results based on the sidebar filter selections.
          Puzzle type, sizes, and difficulty, and completion status will filter the available puzzles, while date played
          will filter the attempted games.
          Press <kbd>Ctrl + Space</kbd> to display autocomplete.
        </p>
        <div ref="editor_container" class="border border-gray-300 rounded-lg overflow-hidden" />
        <div class="flex gap-2">
          <Button variant="secondary" :disabled="loading_preview" @click="run_preview">
            {{ loading_preview ? 'Running...' : 'Preview (100 rows)' }}
          </Button>
          <Button variant="blue" :disabled="loading_download" @click="run_download">
            {{ loading_download ? 'Generating...' : 'Download Parquet' }}
          </Button>
        </div>

        <div v-if="error_message" class="text-red-600 text-sm bg-red-50 p-3 rounded">
          {{ error_message }}
        </div>
      </div>
    </Container>

    <!-- preview results -->
    <Container v-if="preview_data" class="h-full min-h-0 max-h-full overflow-auto">
      <div class="text-sm text-gray-600 mb-2">
        Showing {{ preview_data.rows.length }} of {{ preview_data.total_rows.toLocaleString() }} total rows
      </div>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead v-for="col in preview_data.columns" :key="col" class="text-xs whitespace-nowrap">
              {{ col }}
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow v-for="(row, idx) in preview_data.rows" :key="idx">
            <TableCell v-for="col in preview_data.columns" :key="col" class="text-xs max-w-xs truncate">
              {{ truncate(row[col]) }}
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </Container>
  </div>
</template>

<style scoped>
:deep(.cm-editor) {
  font-size: 18px;
}
:deep(.cm-content),
:deep(.cm-gutters) {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace !important;
}
</style>
