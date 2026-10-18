import { shallowRef } from 'vue'

export const systemPrefersDark = shallowRef(false)

/** One application-level observer, shared by all theme consumers. */
export function observeSystemTheme() {
  const media = window.matchMedia('(prefers-color-scheme: dark)')
  const update = () => {
    systemPrefersDark.value = media.matches
  }
  update()
  media.addEventListener('change', update)
  window.addEventListener('pageshow', update)
  return () => {
    media.removeEventListener('change', update)
    window.removeEventListener('pageshow', update)
  }
}
