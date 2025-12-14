/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */

/**
 * Amelia Design System VitePress Theme
 *
 * Custom theme extending VitePress default theme with:
 * - Custom color palette
 * - Custom typography (Bebas Neue, Barlow Condensed, Source Sans 3, IBM Plex Mono)
 * - Design system token integration
 */

import { h } from 'vue'
import type { Theme } from 'vitepress'
import DefaultTheme from 'vitepress/theme'
import './style.css'
import './custom.css'
import ColorSwatch from './components/ColorSwatch.vue'
import ColorPalette from './components/ColorPalette.vue'
import ColorComparison from './components/ColorComparison.vue'
import AnimatedWorkflowHero from './components/AnimatedWorkflowHero.vue'

export default {
  extends: DefaultTheme,
  Layout: () => {
    return h(DefaultTheme.Layout, null, {
      // Inject animated workflow diagram into the hero image slot
      'home-hero-image': () => h(AnimatedWorkflowHero)
    })
  },
  enhanceApp({ app, router, siteData }) {
    // Register custom components globally
    app.component('ColorSwatch', ColorSwatch)
    app.component('ColorPalette', ColorPalette)
    app.component('ColorComparison', ColorComparison)
    app.component('AnimatedWorkflowHero', AnimatedWorkflowHero)
  }
} satisfies Theme
