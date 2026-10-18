import { createI18n } from 'vue-i18n'
import type { DefineLocaleMessage } from 'vue-i18n'

import enMessages from '@/locales/en/en'
import type { TLanguage } from '@/types/locales'

const messages: Partial<Record<TLanguage, DefineLocaleMessage>> = {
  en: enMessages,
}
const i18n = createI18n({
  legacy: false,
  locale: 'en' as TLanguage,
  fallbackLocale: 'en',
  globalInjection: true,
  messages,
})

const loaders = import.meta.glob<{ default: DefineLocaleMessage }>(
  [
    './locales/*/*.ts',
    // Keep disabled translations in source without shipping unused chunks.
    '!./locales/{en,be,bn,da,fi,sl,sv,ta}/*.ts',
  ]
)
const pending = new Map<TLanguage, Promise<void>>()
let selection = 0

/** Load once per language; a slow earlier selection cannot replace a newer one. */
export const activateLanguage = async (language: TLanguage): Promise<boolean> => {
  const current = ++selection
  if (!i18n.global.availableLocales.includes(language)) {
    let loading = pending.get(language)
    if (!loading) {
      const load = loaders[`./locales/${language}/${language}.ts`]
      if (!load) throw new Error(`Unsupported language: ${language}`)
      loading = load()
        .then((module) => i18n.global.setLocaleMessage(language, module.default))
        .finally(() => pending.delete(language))
      pending.set(language, loading)
    }
    await loading
  }
  if (current !== selection) return false
  i18n.global.locale.value = language
  return true
}

export default i18n
