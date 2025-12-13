<!--
  This Source Code Form is subject to the terms of the Mozilla Public
  License, v. 2.0. If a copy of the MPL was not distributed with this
  file, You can obtain one at https://mozilla.org/MPL/2.0/.
-->

<script setup lang="ts">
import ColorSwatch from './ColorSwatch.vue'

interface ColorObject {
  name: string
  hex: string
  oklch?: string
  usage?: string
}

interface Props {
  colors: ColorObject[]
  columns?: number
  title?: string
}

const props = withDefaults(defineProps<Props>(), {
  columns: 3
})
</script>

<template>
  <div class="color-palette">
    <h3 v-if="title" class="palette-title">{{ title }}</h3>
    <div
      class="palette-grid"
      :style="{
        '--max-columns': columns,
        gridTemplateColumns: `repeat(auto-fill, minmax(280px, 1fr))`
      }"
    >
      <ColorSwatch
        v-for="color in colors"
        :key="color.name"
        :name="color.name"
        :color="color.hex"
        :oklch="color.oklch"
        :usage="color.usage"
      />
    </div>
  </div>
</template>

<style scoped>
.color-palette {
  margin-bottom: 2rem;
}

.palette-title {
  margin-bottom: 1rem;
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--vp-c-text-1);
}

.palette-grid {
  display: grid;
  gap: 1rem;
  max-width: 100%;
}

@media (min-width: 640px) {
  .palette-grid {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  }
}

@media (min-width: 1024px) {
  .palette-grid {
    grid-template-columns: repeat(min(var(--max-columns), auto-fill), minmax(280px, 1fr));
  }
}

@media (max-width: 639px) {
  .palette-grid {
    grid-template-columns: 1fr;
  }
}
</style>
