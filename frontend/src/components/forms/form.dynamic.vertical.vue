<script setup lang="ts">
import Button from "@/components/elements/button.vue";
import { z, ZodEffects, ZodObject } from "zod";
import { type PropType, ref, watch } from "vue";
import { useField, useForm } from "vee-validate";
import { toTypedSchema } from "@vee-validate/zod";

////////////////////////////////////////////////////////////////////////////////
// Vue Props + Emits
type ZodObjectOrEffect = ZodObject<any> | ZodEffects<any>;
const props = defineProps({
  title: String,
  loading: Boolean,
  schema: {
    type: Object as PropType<ZodObjectOrEffect>,
    required: true,
  },
  meta: {
    type: Object as PropType<Record<string, any>>,
    default: {},
    required: false,
  },
  externalErrors: {
    type: Object as PropType<Record<string, any>>,
    default: {},
    required: false,
  },
});
type Schema = z.infer<typeof props.schema>;

const emit = defineEmits<{
  (e: "submit", values: any): void;
}>();

////////////////////////////////////////////////////////////////////////////////
// Generation Functions

/* Get the correct zod schema for the ZodObjectOrEffects */
function getBaseSchema(schema: ZodObjectOrEffect) {
  if (schema instanceof ZodEffects) {
    return schema._def.schema._def.shape();
  } else if (schema instanceof ZodObject) {
    return schema._def.shape();
  }
  throw new Error("Unsupported schema type");
}

/* Generate an object containing the attributes for each input element */
const generate_fields = (schema: Schema) => {
  const fields = Object.keys(schema).map((key) => {
    const itemType = props.meta[key]?.type as string;
    const label = props.meta[key]?.label;

    return {
      name: key,
      type: itemType,
      label,
      placeholder: props.meta[key]?.placeholder || label,
      autocomplete: props.meta[key]?.autocomplete || itemType,
    };
  });
  return fields;
};

/* Generate an object containing {item: useField(ITEM).value} */
const generate_vee_fields = (schema: any) => {
  const raw_object = Object.keys(schema).reduce(
    (res, current) => {
      // The "undefined, { validateOnValueUpdate: false}" stops validation from being run as the user is typing
      res[current] = useField(current, undefined, { validateOnValueUpdate: false }).value;
      return res;
    },
    {} as Record<string, any>,
  );
  return ref(raw_object);
};

// Vue-Validate
const validationSchema = toTypedSchema(props.schema);
const { handleSubmit, errors } = useForm({ validationSchema });
const base_schema = getBaseSchema(props.schema);
const fields = generate_fields(base_schema);
const field_model = generate_vee_fields(base_schema);

const submitForm = handleSubmit(async (values) => {
  emit("submit", values);
});

////////////////////////////////////////////////////////////////////////////////
// Watcher
watch(
  () => props.externalErrors,
  (current, _) => {
    Object.keys(current).forEach((key) => {
      errors.value[key] = current[key].join("<br>");
    });
  },
);
</script>

<template>
  <form @submit.prevent="submitForm">
    <fieldset class="fieldset">
      <div v-for="field in fields" :key="field.name">
        <legend class="fieldset-legend grow">{{ field.label }}</legend>
        <label :for="field.name" class="input">
          <input
            v-model="field_model[field.name]"
            :type="field.type"
            :name="field.name"
            :placeholder="field.placeholder"
            :autocomplete="field.autocomplete"
            required
          />
        </label>
        <p v-if="errors[field.name]" class="text-red-500">
          {{ errors[field.name] }}
        </p>
      </div>
      <Button class="btn btn-neutral mt-4 mx-auto" :loading="loading"> Submit </Button>
    </fieldset>
  </form>
</template>
