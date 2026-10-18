import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'

import TrainingSnapshot from '@/components/Rint/TrainingSnapshot.vue'

const mocks = vi.hoisted(() => ({ get: vi.fn() }))
vi.mock('@/api/authApi', () => ({ default: { get: mocks.get } }))
vi.mock('@/composables/useSports', () => ({
  default: () => ({ sports: ref([{ id: 1, label: 'Running' }]) }),
}))
vi.mock('@/composables/useAuthUser', () => ({
  default: () => ({ imperialUnits: ref(false) }),
}))
const render = () =>
  mount(TrainingSnapshot, {
    global: {
      stubs: {
        'router-link': {
          props: ['to'],
          template:
            '<a :href="typeof to === `string` ? to : to.path + `?from=` + to.query.from + `&to=` + to.query.to"><slot /></a>',
        },
      },
    },
  })

describe('training snapshot', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-01-15T12:00:00'))
    mocks.get.mockReset()
  })
  afterEach(() => vi.useRealTimers())
  it('shows weekly mileage and preserves year boundaries in week drilldowns', async () => {
    mocks.get.mockResolvedValue({
      data: {
        data: [
          {
            week: '2026-01-12',
            sport_id: 1,
            distance_m: 1000,
            activities: 1,
            elapsed_s: 600,
          },
          {
            week: '2026-01-12',
            sport_id: 1,
            distance_m: 2000,
            activities: 2,
            elapsed_s: 1200,
          },
          {
            week: '2025-12-29',
            sport_id: 1,
            distance_m: 5000,
            activities: 1,
            elapsed_s: 3600,
          },
        ],
      },
    })
    const wrapper = render()
    await flushPromises()
    expect(wrapper.find('.snapshot-distance').text()).toContain('3.0')
    expect(wrapper.find('.snapshot-totals strong').text()).toBe('3')
    expect(wrapper.find('.snapshot-totals span').text()).toBe('activities')
    expect(wrapper.findAll('.snapshot-totals strong')[1].text()).toBe('0.5h')
    expect(wrapper.findAll('.snapshot-bars a')).toHaveLength(8)
    expect(wrapper.findAll('.snapshot-bars a')[5].attributes('href')).toContain(
      'from=2025-12-29&to=2026-01-04'
    )
    wrapper.unmount()
  })
  it('shows failure and retries without presenting a false zero', async () => {
    mocks.get
      .mockRejectedValueOnce(new Error('offline'))
      .mockResolvedValueOnce({ data: { data: [] } })
    const wrapper = render()
    await flushPromises()
    expect(wrapper.find('.snapshot-distance').exists()).toBe(false)
    await wrapper.get('button').trigger('click')
    await flushPromises()
    expect(mocks.get).toHaveBeenCalledTimes(2)
    expect(wrapper.find('.snapshot-distance').text()).toContain('0.0')
    expect(wrapper.find('.snapshot-totals strong').text()).toBe('0')
    wrapper.unmount()
  })
})
