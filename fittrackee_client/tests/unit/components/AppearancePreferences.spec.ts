import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'

import UserPreferencesEdition from '@/components/User/ProfileEdition/UserPreferencesEdition.vue'
import { AUTH_USER_STORE } from '@/store/constants'
import type { IAuthUserProfile } from '@/types/user'

const mocks = vi.hoisted(() => ({ dispatch: vi.fn() }))
vi.mock('@/use/useStore', () => ({
  useStore: () => ({ dispatch: mocks.dispatch }),
}))
vi.mock('@/composables/useApp', () => ({
  default: () => ({
    errorMessages: ref(null),
    elevationServices: ref([]),
    elevationsProcessingItems: ref([]),
  }),
}))
vi.mock('@/composables/useAuthUser', () => ({
  default: () => ({ authUserLoading: ref(false) }),
}))

describe('appearance preferences', () => {
  it('changes only appearance after the account finishes loading', async () => {
    const wrapper = mount(UserPreferencesEdition, {
      props: { user: {} as IAuthUserProfile },
      global: {
        mocks: { $t: (key: string) => key },
        stubs: { ErrorMessage: true, TimezoneDropdown: true },
      },
    })
    const preferences = {
      analysis_visibility: 'followers_only',
      calories_visibility: 'followers_only',
      date_format: 'MM/dd/yyyy',
      display_ascent: true,
      hide_profile_in_users_directory: false,
      hr_visibility: 'private',
      imperial_units: true,
      language: 'en',
      manually_approves_followers: true,
      map_visibility: 'private',
      media_visibility: 'followers_only',
      missing_elevations_processing: 'file',
      segments_creation_event: 'only_manual',
      split_workout_charts: true,
      start_elevation_at_zero: false,
      timezone: 'America/New_York',
      use_dark_mode: false,
      use_raw_gpx_speed: false,
      weekm: true,
      workouts_visibility: 'public',
    } as const
    await wrapper.setProps({
      user: { ...preferences, username: 'demo' } as IAuthUserProfile,
    })
    const appearance = wrapper.get<HTMLSelectElement>('#use_dark_mode')
    appearance.element.selectedIndex = 1 // System, with the actual null option value.
    await appearance.trigger('change')
    await wrapper.get('form').trigger('submit')
    expect(mocks.dispatch).toHaveBeenLastCalledWith(
      AUTH_USER_STORE.ACTIONS.UPDATE_USER_PREFERENCES,
      { ...preferences, use_dark_mode: null }
    )
    wrapper.unmount()
  })
})
