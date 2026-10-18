import type { DefineLocaleMessage } from 'vue-i18n'

/** Locale folders share a JSON section contract; administration uses `admin`. */
export const messagesFromSections = (
  sections: Record<string, DefineLocaleMessage>
): DefineLocaleMessage =>
  Object.fromEntries(
    Object.entries(sections).map(([path, messages]) => {
      const section = path.slice(2, -5)
      return [section === 'administration' ? 'admin' : section, messages]
    })
  )
