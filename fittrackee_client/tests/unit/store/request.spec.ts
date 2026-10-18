import { flushPromises } from '@vue/test-utils'
import { AxiosError } from 'axios'
import type { AxiosResponse } from 'axios'
import { describe, expect, it, vi } from 'vitest'

import {
  AUTH_USER_STORE,
  NOTIFICATIONS_STORE,
  ROOT_STORE,
  STATS_STORE,
} from '@/store/constants'
import { actions as authUser } from '@/store/modules/authUser/actions'
import type { IAuthUserState } from '@/store/modules/authUser/types'
import { actions as notifications } from '@/store/modules/notifications/actions'
import type { INotificationsState } from '@/store/modules/notifications/types'
import { actions as root } from '@/store/modules/root/actions'
import type { IRootState } from '@/store/modules/root/types'
import { actions as statistics } from '@/store/modules/statistics/actions'
import type { IStatisticsState } from '@/store/modules/statistics/types'
import { handleApiRequest } from '@/store/request'

const api = vi.hoisted(() => ({ get: vi.fn(), post: vi.fn(), patch: vi.fn() }))
const navigation = vi.hoisted(() => ({ push: vi.fn() }))
vi.mock('@/api/authApi', () => ({ default: api }))
vi.mock('@/api/defaultApi', () => ({ default: api }))
vi.mock('@/router', () => ({ default: navigation }))
vi.mock('@/store', () => ({ default: {} }))

const context = <S>() => ({
  commit: vi.fn(),
  dispatch: vi.fn(),
  getters: {},
  rootGetters: {},
  state: {} as S,
  rootState: {} as IRootState,
})

const response = <T>(data: T, status = 200) =>
  ({ data, status }) as AxiosResponse<T>

describe('shared store requests', () => {
  it('applies a loaded language to the document and store and ignores a stale selection', async () => {
    const store = context<IRootState>()
    await root[ROOT_STORE.ACTIONS.UPDATE_APPLICATION_LANGUAGE](store, 'fr')
    expect(document.documentElement.lang).toBe('fr')
    expect(store.commit).toHaveBeenLastCalledWith(
      ROOT_STORE.MUTATIONS.UPDATE_LANG, 'fr'
    )

    store.commit.mockClear()
    await Promise.all([
      root[ROOT_STORE.ACTIONS.UPDATE_APPLICATION_LANGUAGE](store, 'de'),
      root[ROOT_STORE.ACTIONS.UPDATE_APPLICATION_LANGUAGE](store, 'en'),
    ])
    expect(document.documentElement.lang).toBe('en')
    expect(store.commit.mock.calls).toEqual([
      [ROOT_STORE.MUTATIONS.UPDATE_LANG, 'en'],
    ])
  })

  it('logs in with the returned token and keeps registration and redirects distinct', async () => {
    const store = context<IAuthUserState>()
    store.dispatch.mockResolvedValue(undefined)
    navigation.push.mockResolvedValue(undefined)
    const formData = { email: 'runner@example.org', password: 'example' }

    for (const redirectUrl of ['/progress', undefined]) {
      api.post.mockResolvedValueOnce(
        response({ status: 'success', auth_token: 'new-token' })
      )
      authUser[AUTH_USER_STORE.ACTIONS.LOGIN_OR_REGISTER](store, {
        actionType: 'login', formData, redirectUrl,
      })
      await flushPromises()
      expect(api.post).toHaveBeenLastCalledWith('/auth/login', formData)
      expect(localStorage.getItem('authToken')).toBe('new-token')
      expect(store.dispatch).toHaveBeenLastCalledWith(
        AUTH_USER_STORE.ACTIONS.GET_USER_PROFILE, { updateUI: true }
      )
      expect(navigation.push).toHaveBeenLastCalledWith(redirectUrl || '/')
    }

    store.dispatch.mockClear()
    store.commit.mockClear()
    api.post.mockResolvedValueOnce(response({ status: 'success' }))
    authUser[AUTH_USER_STORE.ACTIONS.LOGIN_OR_REGISTER](store, {
      actionType: 'register', formData,
    })
    await flushPromises()
    expect(api.post).toHaveBeenLastCalledWith('/auth/register', formData)
    expect(navigation.push).toHaveBeenLastCalledWith('/login')
    expect(store.dispatch).not.toHaveBeenCalled()
    expect(store.commit).toHaveBeenLastCalledWith(
      AUTH_USER_STORE.MUTATIONS.UPDATE_IS_REGISTRATION_SUCCESS, true
    )
    localStorage.removeItem('authToken')
  })

  it('preserves success, creation, error, cancellation and expired-token contracts', async () => {
    const store = context<IRootState>()
    const success = vi.fn()
    for (const status of ['success', 'created']) {
      const data = { status, data: { id: 7 } }
      await handleApiRequest(
        store,
        Promise.resolve(response(data)),
        success,
        status
      )
      expect(success).toHaveBeenLastCalledWith(data)
    }
    success.mockClear()

    await handleApiRequest(
      store,
      Promise.resolve(response({ status: 'error' })),
      success
    )
    expect(success).not.toHaveBeenCalled()
    expect(store.commit).toHaveBeenLastCalledWith(
      ROOT_STORE.MUTATIONS.SET_ERROR_MESSAGES,
      'api.ERROR.UNKNOWN'
    )

    for (const message of ['offline', 'canceled']) {
      store.commit.mockClear()
      await handleApiRequest(
        store,
        Promise.reject(new AxiosError(message)),
        success
      )
      if (message === 'canceled') {
        expect(store.commit).not.toHaveBeenCalled()
      } else {
        expect(store.commit).toHaveBeenCalledWith(
          ROOT_STORE.MUTATIONS.SET_ERROR_MESSAGES,
          'api.ERROR.offline'
        )
      }
    }

    localStorage.setItem('authToken', 'expired')
    await handleApiRequest(
      store,
      Promise.reject(
        new AxiosError(
          'unauthorized',
          undefined,
          undefined,
          undefined,
          response({ error: 'invalid_token' }, 401)
        )
      ),
      success
    )
    expect(localStorage.getItem('authToken')).toBeNull()
    expect(store.dispatch).toHaveBeenCalledWith(
      AUTH_USER_STORE.ACTIONS.CHECK_AUTH_USER
    )
    expect(success).not.toHaveBeenCalled()

    await handleApiRequest(
      store,
      Promise.resolve(response({ status: 'success' })),
      () => {
        throw new Error('invalid response')
      }
    )
    expect(store.commit).toHaveBeenLastCalledWith(
      ROOT_STORE.MUTATIONS.SET_ERROR_MESSAGES,
      'api.ERROR.invalid response'
    )
  })

  it('loads notifications, preserves pagination, and refreshes after marking read', async () => {
    const store = context<INotificationsState>()
    const query = { page: 2 }
    const data = {
      status: 'success',
      notifications: [{ id: 7 }],
      pagination: { page: 2, total: 11 },
    }
    api.get.mockResolvedValueOnce(response(data))
    await notifications[NOTIFICATIONS_STORE.ACTIONS.GET_NOTIFICATIONS](
      store,
      query
    )
    expect(api.get).toHaveBeenLastCalledWith('notifications', { params: query })
    expect(store.commit.mock.calls).toEqual([
      [ROOT_STORE.MUTATIONS.EMPTY_ERROR_MESSAGES],
      [NOTIFICATIONS_STORE.MUTATIONS.UPDATE_NOTIFICATIONS, data.notifications],
      [NOTIFICATIONS_STORE.MUTATIONS.UPDATE_PAGINATION, data.pagination],
    ])

    api.patch.mockResolvedValueOnce(response({ status: 'success' }))
    notifications[NOTIFICATIONS_STORE.ACTIONS.UPDATE_STATUS](store, {
      notificationId: 7,
      markedAsRead: true,
      currentQuery: query,
    })
    await flushPromises()
    expect(api.patch).toHaveBeenLastCalledWith('notifications/7', {
      read_status: true,
    })
    expect(store.dispatch.mock.calls).toEqual([
      [NOTIFICATIONS_STORE.ACTIONS.GET_NOTIFICATIONS, query],
      [NOTIFICATIONS_STORE.ACTIONS.GET_UNREAD_STATUS],
    ])
  })

  it('keeps statistics loading state balanced after success, failure and cancellation', async () => {
    for (const outcome of ['success', 'offline', 'canceled']) {
      const store = context<IStatisticsState>()
      if (outcome === 'success') {
        api.get.mockResolvedValueOnce(
          response({
            status: 'success',
            data: { statistics: { distance: 42 }, total_workouts: 3 },
          })
        )
      } else {
        api.get.mockRejectedValueOnce(new AxiosError(outcome))
      }
      statistics[STATS_STORE.ACTIONS.GET_USER_SPORT_STATS](store, {
        username: 'runner',
        sportId: 2,
      })
      await flushPromises()
      expect(api.get).toHaveBeenLastCalledWith('stats/runner/by_sport', {
        params: { sport_id: 2 },
      })
      expect(store.commit.mock.calls.slice(0, 2)).toEqual([
        [ROOT_STORE.MUTATIONS.EMPTY_ERROR_MESSAGES],
        [STATS_STORE.MUTATIONS.UPDATE_STATS_LOADING, true],
      ])
      expect(store.commit).toHaveBeenLastCalledWith(
        STATS_STORE.MUTATIONS.UPDATE_STATS_LOADING,
        false
      )
      if (outcome === 'success') {
        expect(store.commit).toHaveBeenCalledWith(
          STATS_STORE.MUTATIONS.UPDATE_USER_SPORT_STATS,
          { distance: 42 }
        )
        expect(store.commit).toHaveBeenCalledWith(
          STATS_STORE.MUTATIONS.UPDATE_TOTAL_WORKOUTS,
          3
        )
      }
    }
  })
})
