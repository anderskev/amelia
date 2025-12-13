<!--
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
-->

<script setup lang="ts">
import { ref } from 'vue'

interface Props {
  color: string
  name: string
  oklch?: string
  usage?: string
}

const props = defineProps<Props>()

const copied = ref(false)

const copyToClipboard = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch (err) {
    console.error('Failed to copy:', err)
  }
}
</script>

<template>
  <div class="color-swatch">
    <div
      class="color-preview"
      :style="{ backgroundColor: color }"
      :title="`Click to copy ${color}`"
      @click="copyToClipboard(color)"
    >
      <div v-if="copied" class="copied-feedback">
        Copied!
      </div>
    </div>

    <div class="color-info">
      <div class="color-name">
        {{ name }}
      </div>

      <div
        class="color-hex"
        :title="'Click to copy ' + color"
        @click="copyToClipboard(color)"
      >
        {{ color }}
      </div>

      <div v-if="oklch" class="color-oklch">
        {{ oklch }}
      </div>

      <div v-if="usage" class="color-usage">
        {{ usage }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.color-swatch {
  border: 1px solid var(--vp-c-border);
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.2s ease;
  background-color: var(--vp-c-bg-soft);
}

.color-swatch:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.color-preview {
  height: 80px;
  width: 100%;
  cursor: pointer;
  position: relative;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-left: none;
  border-right: none;
  border-top: none;
  transition: opacity 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.color-preview:hover {
  opacity: 0.9;
}

.color-preview:active {
  opacity: 0.8;
}

.copied-feedback {
  background-color: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  animation: fadeInOut 2s ease;
}

@keyframes fadeInOut {
  0% {
    opacity: 0;
    transform: scale(0.9);
  }
  15% {
    opacity: 1;
    transform: scale(1);
  }
  85% {
    opacity: 1;
    transform: scale(1);
  }
  100% {
    opacity: 0;
    transform: scale(0.9);
  }
}

.color-info {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.color-name {
  font-family: var(--vp-font-family-mono);
  font-size: 14px;
  font-weight: 600;
  color: var(--vp-c-text-1);
  word-break: break-word;
}

.color-hex {
  font-family: var(--vp-font-family-mono);
  font-size: 13px;
  color: var(--vp-c-text-2);
  cursor: pointer;
  transition: color 0.2s ease;
  user-select: all;
  width: fit-content;
}

.color-hex:hover {
  color: var(--vp-c-brand-1);
}

.color-oklch {
  font-family: var(--vp-font-family-mono);
  font-size: 12px;
  color: var(--vp-c-text-3);
  word-break: break-all;
}

.color-usage {
  font-size: 13px;
  color: var(--vp-c-text-2);
  line-height: 1.5;
  margin-top: 4px;
  padding-top: 8px;
  border-top: 1px solid var(--vp-c-divider);
}
</style>
