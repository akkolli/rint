<template>
  <div class="about-text">
    <div>
      <p class="r-eyebrow">Your fitness, your data</p>
      <h1 class="r-page-title">Rint</h1>
      <p class="about-intro">
        Track your activities, explore your training and keep your history in
        one place.
      </p>
      <p>
        Rint is an independent, open-source fork of FitTrackee, with detailed
        activity analysis and companion iPhone and Apple Watch apps.
      </p>
      <p v-if="sourceLink">
        <a :href="sourceLink" target="_blank" rel="noopener noreferrer"
          >Rint source code</a
        >
      </p>
      <p>
        <i class="fa fa-book fa-padding" aria-hidden="true"></i>
        <a
          class="documentation-link"
          :href="documentationLink"
          target="_blank"
          rel="noopener noreferrer"
        >
          FitTrackee documentation
        </a>
      </p>
      <p>
        <img
          class="codeberg-logo"
          :src="'/img/codeberg.svg'"
          alt="Codeberg Logo"
        />
        <a
          href="https://codeberg.org/FitTrackee/FitTrackee"
          target="_blank"
          rel="noopener noreferrer"
        >
          FitTrackee source code
        </a>
      </p>
      <p>
        <i class="fa fa-balance-scale fa-padding" aria-hidden="true"></i>
        <i18n-t keypath="about.FITTRACKEE_LICENSE">
          <a
            href="https://choosealicense.com/licenses/agpl-3.0/"
            target="_blank"
            rel="noopener noreferrer"
            >AGPLv3</a
          >
        </i18n-t>
      </p>
      <div v-if="appConfig.admin_contact">
        <i class="fa fa-envelope-o fa-padding" aria-hidden="true"></i>
        <a :href="`mailto:${appConfig.admin_contact}`">
          {{ $t('about.CONTACT_ADMIN') }}
        </a>
      </div>
      <div v-if="weatherProvider && weatherProvider.name">
        {{ $t('about.WEATHER_DATA_FROM') }}
        <a :href="weatherProvider.url" target="_blank" rel="nofollow noopener">
          {{ weatherProvider.name }}
        </a>
      </div>
      <div v-if="elevationServices.length > 0">
        {{ $t('about.ELEVATION_DATA_FROM') }} {{ elevationServices.join(', ') }}
      </div>
      <template v-if="appConfig.about">
        <p class="about-instance">{{ $t('about.ABOUT_THIS_INSTANCE') }}</p>
        <div v-html="convertToMarkdown(appConfig.about)" />
      </template>
    </div>
  </div>
</template>

<script lang="ts" setup>
  import { computed } from 'vue'
  import type { ComputedRef } from 'vue'

  import useApp from '@/composables/useApp'
  import { convertToMarkdown } from '@/utils/inputs'

  const { appConfig, elevationServices, appLanguage } = useApp()
  // Deployment owners supply the corresponding fork source, not an upstream URL.
  const sourceLink = (() => {
    try {
      const url = new URL(import.meta.env.VITE_RINT_SOURCE_URL || '')
      return ['https:', 'http:'].includes(url.protocol) ? url.href : ''
    } catch {
      return ''
    }
  })()

  const weatherProvider: ComputedRef<Record<string, string>> = computed(() =>
    get_weather_provider()
  )
  const documentationLink: ComputedRef<string> = computed(() =>
    get_documentation_link()
  )

  function get_weather_provider() {
    const weatherProvider: Record<string, string> = {}
    if (appConfig.value.weather_provider === 'visualcrossing') {
      weatherProvider['name'] = 'Visual Crossing'
      weatherProvider['url'] = 'https://www.visualcrossing.com'
    }
    return weatherProvider
  }

  function get_documentation_link() {
    let link = 'https://docs.fittrackee.org/'
    if (appLanguage.value === 'fr') {
      link += 'fr/'
    }
    return link
  }
</script>

<style lang="scss" scoped>
  @use '~@/scss/vars.scss' as *;

  .about-text {
    max-width: 650px;
    margin: 0 auto;
    padding: 32px;
    color: var(--r-ink);
    line-height: 1.65;
    .about-intro {
      font-size: 20px;
      line-height: 1.5;
      margin: 20px 0;
    }
    .r-eyebrow {
      margin-bottom: 10px;
    }
    p {
      color: var(--r-muted);
    }
    a {
      color: var(--r-action);
    }
    .codeberg-logo {
      width: 18px;
      vertical-align: middle;
    }
    @media screen and (max-width: $small-limit) {
      margin-top: 0;
      margin-right: 0;
      padding-bottom: 0;
    }
    .fa-padding,
    .codeberg-logo {
      padding-right: $default-padding;
    }
    .about-instance {
      font-weight: bold;
      margin-top: $default-margin * 3;
    }
  }
</style>
