import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'

import Timeline from '@/components/Dashboard/Timeline.vue'
import type { IAuthUserProfile } from '@/types/user'

const mocks = vi.hoisted(() => ({ get: vi.fn() }))
vi.mock('@/api/authApi', () => ({ default: { get: mocks.get } }))
vi.mock('@/composables/useAuthUser', () => ({
  default: () => ({ dateFormat: ref('MM/dd/yyyy') }),
}))
const render = () =>
  mount(Timeline, {
    props: {
      authUser: { username: 'demo', nb_workouts: 9 } as IAuthUserProfile,
      sports: [],
    },
    global: {
      mocks: { $t: (key: string) => key },
      stubs: {
        WorkoutCard: {
          props: ['workout'],
          template: '<article>{{ workout?.title || `Loading` }}</article>',
        },
        NoWorkouts: { template: '<p>No activities</p>' },
      },
    },
  })
const response = (title: string, more = true) => ({
  data: {
    status: 'success',
    data: { workouts: [{ id: title, title }] },
    pagination: { has_next: more },
  },
})

describe('feed recovery', () => {
  beforeEach(() => mocks.get.mockReset())
  it('replaces initial skeletons with an actionable error and retries page one', async () => {
    mocks.get
      .mockRejectedValueOnce(new Error('offline'))
      .mockResolvedValueOnce(response('Recovered', false))
    const wrapper = render()
    await flushPromises()
    expect(wrapper.text()).toContain('Your feed couldn’t load')
    expect(wrapper.findAll('article')).toHaveLength(0)
    await wrapper.get('button').trigger('click')
    await flushPromises()
    expect(mocks.get.mock.calls[1][1].params.page).toBe(1)
    expect(wrapper.text()).toContain('Recovered')
    wrapper.unmount()
  })
  it('retains existing activities and retries the failed page without skipping it', async () => {
    mocks.get
      .mockResolvedValueOnce(response('First'))
      .mockRejectedValueOnce(new Error('offline'))
      .mockResolvedValueOnce(response('Second', false))
    const wrapper = render()
    await flushPromises()
    await wrapper.get('.more-workouts button').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('First')
    await wrapper.get('.feed-error button').trigger('click')
    await flushPromises()
    expect(mocks.get.mock.calls.map((call) => call[1].params.page)).toEqual([
      1, 2, 2,
    ])
    expect(wrapper.findAll('article')).toHaveLength(2)
    expect(wrapper.find('.more-workouts').exists()).toBe(false)
    wrapper.unmount()
  })
})
