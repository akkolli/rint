import { mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent } from 'vue'

import RouteTrace from '@/components/Rint/RouteTrace.vue'

const routeMap = defineComponent({
  name: 'ActivityRouteMap',
  props: ['points', 'selectedTime', 'units'],
  emits: ['select-time', 'metric-change'],
  template: '<div />',
})

describe('route and chart connection', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'IntersectionObserver',
      class {
        observe() {}
        disconnect() {}
      }
    )
  })
  afterEach(() => vi.unstubAllGlobals())

  it('forwards route inspection, metric choice and distance units through the lazy map', () => {
    const wrapper = mount(RouteTrace, {
      props: {
        points: [
          { t: 0, d: 0, lat: 40, lon: -73 },
          { t: 10, d: 30, lat: 40.001, lon: -73 },
        ],
        selectedTime: 5,
        units: 'mi',
      },
      global: { stubs: { ActivityRouteMap: routeMap } },
    })
    const map = wrapper.getComponent(routeMap)
    expect(map.props('units')).toBe('mi')
    expect(map.props('selectedTime')).toBe(5)
    map.vm.$emit('select-time', 10)
    map.vm.$emit('metric-change', 'heart_rate')
    expect(wrapper.emitted('select-time')).toEqual([[10]])
    expect(wrapper.emitted('metric-change')).toEqual([['heart_rate']])
    wrapper.unmount()
  })

  it('uses a compact missing-route state while retaining sensor-only workouts', () => {
    const wrapper = mount(RouteTrace, {
      props: { points: [{ t: 0, d: 0, heart_rate: 140 }] },
    })
    expect(wrapper.classes()).toContain('route-trace--compact')
    expect(wrapper.text()).toContain('Your metrics still count')
    expect(wrapper.findComponent(routeMap).exists()).toBe(false)
    wrapper.unmount()
  })
})
