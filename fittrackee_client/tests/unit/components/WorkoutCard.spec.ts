import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'

import Distance from '@/components/Common/Distance.vue'
import WorkoutCard from '@/components/Workout/WorkoutCard.vue'
import type { IUserProfile } from '@/types/user'
import type { IWorkout } from '@/types/workouts'

const mocks = vi.hoisted(() => ({
  push: vi.fn(),
  post: vi.fn().mockResolvedValue({}),
}))
vi.mock('@/router', () => ({ default: { push: mocks.push } }))
vi.mock('@/api/authApi', () => ({ default: { post: mocks.post } }))
vi.mock('@/composables/useApp', () => ({
  default: () => ({ locale: ref(undefined) }),
}))

const render = (changes: Partial<IWorkout> = {}, imperial = false) =>
  mount(WorkoutCard, {
    props: {
      user: { username: 'Runner' } as IUserProfile,
      dateFormat: 'MM/dd/yyyy',
      timezone: 'UTC',
      useImperialUnits: imperial,
      sport: { id: 5, label: 'Running' } as never,
      workout: {
        id: 'indoor',
        title: 'Indoor Run',
        workout_date: '2026-10-16T14:00:00Z',
        distance: 5,
        moving: '0:29:00',
        duration: '0:30:00',
        ave_pace: '0:05:52.32',
        ave_hr: 140,
        ascent: null,
        with_stream: true,
        with_geometry: false,
        likes_count: 0,
        liked: false,
        media_attachments: [],
        ...changes,
      } as IWorkout,
    },
    global: {
      components: { Distance },
      stubs: {
        RouterLink: {
          props: ['to'],
          template: '<a @click.prevent><slot /></a>',
        },
        UserPicture: true,
        VisibilityIcon: true,
        RouteTrace: true,
        StaticMap: true,
      },
    },
  })

describe('workout feed cards', () => {
  it('keeps original timing precision until imperial pace display rounding', () => {
    const wrapper = render({ distance: 1, moving: '0:05:52.32' }, true)
    expect(wrapper.get('.workout-data').text()).toContain('09:27')
    expect(wrapper.get('.workout-data').text()).toContain('/mi')
    expect(wrapper.findAll('.workout-data > div')).toHaveLength(4)
    wrapper.unmount()
  })
  it('labels the elapsed basis when moving time is unavailable', () => {
    const wrapper = render({ moving: null })
    expect(wrapper.get('.workout-data').text()).toContain('Elapsed time')
    expect(wrapper.get('.workout-data').text()).toContain('Elapsed pace')
    expect(wrapper.get('.workout-data').text()).toContain('06:00')
    wrapper.unmount()
  })
  it('does not invent a pace or reserve a route row when neither is available', () => {
    const wrapper = render({ distance: 0 })
    expect(wrapper.text()).not.toContain('Moving pace')
    expect(wrapper.find('.route-link').exists()).toBe(false)
    expect(wrapper.text()).not.toContain('No route shared')
    expect(wrapper.findAll('.workout-data > div')).toHaveLength(3)
    wrapper.unmount()
  })
  it('does not turn a subsecond recording into a misleading pace', () => {
    const wrapper = render({ distance: 0.05, moving: '0:00:00.05' })
    expect(wrapper.text()).not.toContain('Moving pace')
    expect(wrapper.findAll('.workout-data > div')).toHaveLength(3)
    wrapper.unmount()
  })
  it('opens card space but keeps profile and social controls independent', async () => {
    mocks.push.mockClear()
    const wrapper = render()
    await wrapper.get('.card-avatar').trigger('click')
    expect(mocks.push).not.toHaveBeenCalled()
    await wrapper.get('.feed-actions button').trigger('click')
    await flushPromises()
    expect(mocks.post).toHaveBeenCalledWith('workouts/indoor/like')
    expect(wrapper.get('.feed-actions button').attributes('aria-pressed')).toBe(
      'true'
    )
    expect(mocks.push).not.toHaveBeenCalled()
    await wrapper.get('article').trigger('click')
    expect(mocks.push).toHaveBeenCalledWith({
      name: 'Workout',
      params: { workoutId: 'indoor' },
    })
    wrapper.unmount()
  })
})
