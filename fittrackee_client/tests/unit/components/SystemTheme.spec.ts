import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { reactive } from 'vue'

import useApp from '@/composables/useApp'
import { ROOT_STORE } from '@/store/constants'
import { observeSystemTheme } from '@/utils/systemTheme'

const mock = vi.hoisted(() => ({ getters: {} as Record<string, unknown> }))
vi.mock('@/use/useStore', () => ({
  useStore: () => ({ getters: mock.getters }),
}))

describe('system appearance', () => {
  let dark = false
  let media: EventTarget
  let stop: (() => void) | undefined
  beforeEach(() => {
    dark = false
    media = new EventTarget()
    Object.defineProperty(media, 'matches', { get: () => dark })
    vi.stubGlobal(
      'matchMedia',
      vi.fn(() => media)
    )
    mock.getters = reactive({ [ROOT_STORE.GETTERS.DARK_MODE]: null })
  })
  afterEach(() => {
    stop?.()
    stop = undefined
    vi.unstubAllGlobals()
  })

  it('follows light/dark system changes without reloading the app', () => {
    stop = observeSystemTheme()
    const { darkTheme } = useApp()
    expect(darkTheme.value).toBe(false)
    dark = true
    media.dispatchEvent(new Event('change'))
    expect(darkTheme.value).toBe(true)
    dark = false
    media.dispatchEvent(new Event('change'))
    expect(darkTheme.value).toBe(false)
  })
  it('reads dark appearance at startup and when returning to a cached page', () => {
    dark = true
    stop = observeSystemTheme()
    const { darkTheme } = useApp()
    expect(darkTheme.value).toBe(true)
    dark = false
    window.dispatchEvent(new Event('pageshow'))
    expect(darkTheme.value).toBe(false)
  })
  it('preserves explicit choices and immediately resumes system matching', () => {
    stop = observeSystemTheme()
    const { darkTheme } = useApp()
    mock.getters[ROOT_STORE.GETTERS.DARK_MODE] = true
    expect(darkTheme.value).toBe(true)
    dark = true
    media.dispatchEvent(new Event('change'))
    mock.getters[ROOT_STORE.GETTERS.DARK_MODE] = false
    expect(darkTheme.value).toBe(false)
    mock.getters[ROOT_STORE.GETTERS.DARK_MODE] = null
    expect(darkTheme.value).toBe(true)
  })
  it('removes listeners when the app is unmounted', () => {
    stop = observeSystemTheme()
    const { darkTheme } = useApp()
    stop()
    dark = true
    media.dispatchEvent(new Event('change'))
    window.dispatchEvent(new Event('pageshow'))
    expect(darkTheme.value).toBe(false)
  })
})
