import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { TLanguage } from '@/types/locales'
import { languageLabels } from '@/utils/locales'

const sections = [
  'about', 'admin', 'api', 'buttons', 'common', 'dashboard', 'equipment_types',
  'equipments', 'error', 'notifications', 'oauth2', 'privacy_policy', 'sports',
  'statistics', 'user', 'visibility_levels', 'workouts',
]

describe('locale loading', () => {
  beforeEach(() => vi.resetModules())

  it('loads every supported language with the original JSON sections and caches it', async () => {
    const { default: i18n, activateLanguage } = await import('@/i18n')
    const originals = import.meta.glob<Record<string, unknown>>(
      '../../../src/locales/*/*.json', { eager: true, import: 'default' }
    )
    expect(i18n.global.availableLocales).toEqual(['en'])
    for (const language of Object.keys(languageLabels) as TLanguage[]) {
      expect(await activateLanguage(language)).toBe(true)
      expect(i18n.global.locale.value).toBe(language)
      const messages = i18n.global.getLocaleMessage(language)
      expect(Object.keys(messages).sort()).toEqual(sections)
      for (const section of sections) {
        const filename = section === 'admin' ? 'administration' : section
        expect(messages[section]).toEqual(
          originals[`../../../src/locales/${language}/${filename}.json`]
        )
      }
      expect(await activateLanguage(language)).toBe(true)
      expect(i18n.global.getLocaleMessage(language)).toBe(messages)
    }
    await activateLanguage('en')
  })

  it('keeps the latest selection when asynchronous language changes overlap', async () => {
    const { default: i18n, activateLanguage } = await import('@/i18n')
    // A ready language supersedes an earlier selection in the same event loop.
    const selections = [activateLanguage('fr'), activateLanguage('de'), activateLanguage('en')]
    expect(await Promise.all(selections)).toEqual([false, false, true])
    expect(i18n.global.locale.value).toBe('en')
  })
})
