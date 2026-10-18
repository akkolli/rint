import type { ActionContext, ActionTree } from 'vuex'

import authApi from '@/api/authApi'
import router from '@/router'
import { AUTH_USER_STORE, ROOT_STORE, USERS_STORE } from '@/store/constants'
import type { IAuthUserState } from '@/store/modules/authUser/types'
import type { IRootState } from '@/store/modules/root/types'
import type { IUsersActions, IUsersState } from '@/store/modules/users/types'
import { handleApiRequest } from '@/store/request'
import type { IQueuedTasksPayload } from '@/types/application.ts'
import type {
  IAdminUserPayload,
  IUserDeletionPayload,
  IUserRelationshipActionPayload,
  IUserRelationshipsPayload,
  TUsersPayload,
} from '@/types/user'
import { handleError } from '@/utils'

export const deleteUserAccount = (
  context:
    | ActionContext<IAuthUserState, IRootState>
    | ActionContext<IUsersState, IRootState>,
  payload: IUserDeletionPayload
): void => {
  context.commit(ROOT_STORE.MUTATIONS.EMPTY_ERROR_MESSAGES)
  authApi
    .delete(`users/${payload.username}`)
    .then((res) => {
      if (res.status === 204) {
        if (payload.fromAdmin) {
          router.push('/admin/users')
        } else {
          context
            .dispatch(AUTH_USER_STORE.ACTIONS.LOGOUT)
            .then(() => router.push('/'))
        }
      } else {
        handleError(context, null)
      }
    })
    .catch((error) => handleError(context, error))
}

const getUsers = (
  context:
    | ActionContext<IAuthUserState, IRootState>
    | ActionContext<IUsersState, IRootState>,
  payload: TUsersPayload,
  forAdmin = false
): void => {
  context.commit(ROOT_STORE.MUTATIONS.EMPTY_ERROR_MESSAGES)
  context.commit(USERS_STORE.MUTATIONS.UPDATE_USERS_LOADING, true)
  if (forAdmin) {
    payload.with_inactive = 'true'
    payload.with_hidden = 'true'
    payload.with_suspended = 'true'
  }
  handleApiRequest(
    context,
    authApi.get('users', { params: payload }),
    (data) => {
      context.commit(USERS_STORE.MUTATIONS.UPDATE_USERS, data.data.users)
      context.commit(
        USERS_STORE.MUTATIONS.UPDATE_USERS_PAGINATION,
        data.pagination
      )
    }
  ).finally(() =>
    context.commit(USERS_STORE.MUTATIONS.UPDATE_USERS_LOADING, false)
  )
}

export const actions: ActionTree<IUsersState, IRootState> & IUsersActions = {
  [USERS_STORE.ACTIONS.EMPTY_USER](
    context: ActionContext<IUsersState, IRootState>
  ): void {
    context.commit(ROOT_STORE.MUTATIONS.EMPTY_ERROR_MESSAGES)
    context.commit(USERS_STORE.MUTATIONS.UPDATE_USER, {})
  },
  [USERS_STORE.ACTIONS.EMPTY_USERS](
    context: ActionContext<IUsersState, IRootState>
  ): void {
    context.commit(ROOT_STORE.MUTATIONS.EMPTY_ERROR_MESSAGES)
    context.commit(USERS_STORE.MUTATIONS.UPDATE_USERS, [])
    context.commit(USERS_STORE.MUTATIONS.UPDATE_USERS_PAGINATION, {})
  },
  [USERS_STORE.ACTIONS.EMPTY_RELATIONSHIPS](
    context: ActionContext<IUsersState, IRootState>
  ): void {
    context.commit(ROOT_STORE.MUTATIONS.EMPTY_ERROR_MESSAGES)
    context.commit(USERS_STORE.MUTATIONS.UPDATE_USER_RELATIONSHIPS, [])
    context.commit(USERS_STORE.MUTATIONS.UPDATE_USERS_PAGINATION, {})
  },
  [USERS_STORE.ACTIONS.GET_USER](
    context: ActionContext<IUsersState, IRootState>,
    username: string
  ): void {
    context.commit(ROOT_STORE.MUTATIONS.EMPTY_ERROR_MESSAGES)
    context.commit(USERS_STORE.MUTATIONS.UPDATE_USERS_LOADING, true)
    handleApiRequest(context, authApi.get(`users/${username}`), (data) => {
      context.commit(USERS_STORE.MUTATIONS.UPDATE_USER, data.data.users[0])
    }).finally(() =>
      context.commit(USERS_STORE.MUTATIONS.UPDATE_USERS_LOADING, false)
    )
  },
  [USERS_STORE.ACTIONS.GET_USER_SANCTIONS](
    context: ActionContext<IUsersState, IRootState>,
    payload: TUsersPayload
  ): void {
    context.commit(ROOT_STORE.MUTATIONS.EMPTY_ERROR_MESSAGES)
    context.commit(USERS_STORE.MUTATIONS.UPDATE_USER_SANCTIONS_LOADING, true)
    const { username, ...params } = payload
    handleApiRequest(
      context,
      authApi.get(`users/${username}/sanctions`, { params }),
      (data) => {
        context.commit(
          USERS_STORE.MUTATIONS.UPDATE_USER_SANCTIONS,
          data.data.sanctions
        )
        context.commit(
          USERS_STORE.MUTATIONS.UPDATE_USER_SANCTIONS_PAGINATION,
          data.pagination
        )
      }
    ).finally(() =>
      context.commit(USERS_STORE.MUTATIONS.UPDATE_USER_SANCTIONS_LOADING, false)
    )
  },
  [USERS_STORE.ACTIONS.GET_USER_WORKOUTS](
    context: ActionContext<IUsersState, IRootState>,
    username: string
  ): void {
    context.commit(ROOT_STORE.MUTATIONS.EMPTY_ERROR_MESSAGES)
    context.commit(USERS_STORE.MUTATIONS.UPDATE_USER_WORKOUTS_LOADING, true)
    handleApiRequest(
      context,
      authApi.get(`users/${username}/workouts`),
      (data) => {
        context.commit(
          USERS_STORE.MUTATIONS.UPDATE_USER_WORKOUTS,
          data.data.workouts
        )
      }
    ).finally(() =>
      context.commit(USERS_STORE.MUTATIONS.UPDATE_USER_WORKOUTS_LOADING, false)
    )
  },
  [USERS_STORE.ACTIONS.GET_USERS](
    context: ActionContext<IUsersState, IRootState>,
    payload: TUsersPayload
  ): void {
    getUsers(context, payload, false)
  },
  [USERS_STORE.ACTIONS.GET_USERS_FOR_ADMIN](
    context: ActionContext<IUsersState, IRootState>,
    payload: TUsersPayload
  ): void {
    getUsers(context, payload, true)
  },
  [USERS_STORE.ACTIONS.UPDATE_USER](
    context: ActionContext<IUsersState, IRootState>,
    payload: IAdminUserPayload
  ): void {
    context.commit(ROOT_STORE.MUTATIONS.EMPTY_ERROR_MESSAGES)
    context.commit(USERS_STORE.MUTATIONS.UPDATE_IS_SUCCESS, false)
    const data: Record<string, boolean | string | number | undefined> = {}
    if (payload.role !== undefined) {
      data.role = payload.role
    }
    if (payload.resetPassword) {
      data.reset_password = payload.resetPassword
    }
    if ('activate' in payload && payload.activate !== undefined) {
      data.activate = payload.activate
    }
    if (payload.new_email !== undefined) {
      data.new_email = payload.new_email
    }
    handleApiRequest(
      context,
      authApi.patch(`users/${payload.username}`, data),
      (data) => {
        context.commit(
          USERS_STORE.MUTATIONS.UPDATE_USER_IN_USERS,
          data.data.users[0]
        )
        if (payload.resetPassword || payload.new_email || payload.role) {
          context.commit(USERS_STORE.MUTATIONS.UPDATE_IS_SUCCESS, true)
        }
        if (payload.activate || payload.new_email) {
          context.commit(USERS_STORE.MUTATIONS.UPDATE_USER, data.data.users[0])
        }
      }
    ).finally(() =>
      context.commit(USERS_STORE.MUTATIONS.UPDATE_USERS_LOADING, false)
    )
  },
  [USERS_STORE.ACTIONS.UPDATE_RELATIONSHIP](
    context: ActionContext<IUsersState, IRootState>,
    payload: IUserRelationshipActionPayload
  ): void {
    context.commit(ROOT_STORE.MUTATIONS.EMPTY_ERROR_MESSAGES)
    context.commit(USERS_STORE.MUTATIONS.UPDATE_USERS_LOADING, true)
    authApi
      .post(`users/${payload.username}/${payload.action}`)
      .then((res) => {
        if (res.data.status === 'success') {
          authApi.get(`users/${payload.username}`).then((res) => {
            if (res.data.status === 'success') {
              if (payload.from === 'blocked-users') {
                context.dispatch(
                  AUTH_USER_STORE.ACTIONS.GET_BLOCKED_USERS,
                  payload.payload
                )
                return
              }
              context.commit(
                payload.from === 'userInfos'
                  ? USERS_STORE.MUTATIONS.UPDATE_USER
                  : payload.from === 'userCard'
                    ? USERS_STORE.MUTATIONS.UPDATE_USER_IN_USERS
                    : USERS_STORE.MUTATIONS.UPDATE_USER_IN_RELATIONSHIPS,
                res.data.data.users[0]
              )
              context.dispatch(AUTH_USER_STORE.ACTIONS.GET_USER_PROFILE, {
                light: true,
              })
            } else {
              handleError(context, null)
            }
          })
        } else {
          handleError(context, null)
        }
      })
      .catch((error) => handleError(context, error))
      .finally(() =>
        context.commit(USERS_STORE.MUTATIONS.UPDATE_USERS_LOADING, false)
      )
  },
  [USERS_STORE.ACTIONS.GET_RELATIONSHIPS](
    context: ActionContext<IUsersState, IRootState>,
    payload: IUserRelationshipsPayload
  ): void {
    context.commit(ROOT_STORE.MUTATIONS.EMPTY_ERROR_MESSAGES)
    context.commit(USERS_STORE.MUTATIONS.UPDATE_USERS_LOADING, true)
    handleApiRequest(
      context,
      authApi.get(`users/${payload.username}/${payload.relationship}`, {
        params: { page: payload.page },
      }),
      (data) => {
        context.commit(
          USERS_STORE.MUTATIONS.UPDATE_USER_RELATIONSHIPS,
          data.data[payload.relationship]
        )
        context.commit(
          USERS_STORE.MUTATIONS.UPDATE_USERS_PAGINATION,
          data.pagination
        )
      }
    ).finally(() =>
      context.commit(USERS_STORE.MUTATIONS.UPDATE_USERS_LOADING, false)
    )
  },
  [USERS_STORE.ACTIONS.DELETE_USER_ACCOUNT](
    context: ActionContext<IUsersState, IRootState>,
    payload: IUserDeletionPayload
  ): void {
    deleteUserAccount(context, {
      username: payload.username,
      fromAdmin: true,
    })
  },
  [USERS_STORE.ACTIONS.GET_USERS_QUEUED_TASKS_COUNT](
    context: ActionContext<IUsersState, IRootState>
  ): void {
    context.commit(ROOT_STORE.MUTATIONS.EMPTY_ERROR_MESSAGES)
    handleApiRequest(context, authApi.get('users/tasks/queued'), (data) => {
      context.commit(
        USERS_STORE.MUTATIONS.UPDATE_USERS_QUEUED_TASKS_COUNTS,
        data.counts
      )
    })
  },
  [USERS_STORE.ACTIONS.GET_USERS_QUEUED_TASKS_LIST](
    context: ActionContext<IUsersState, IRootState>,
    payload: IQueuedTasksPayload
  ): void {
    context.commit(ROOT_STORE.MUTATIONS.EMPTY_ERROR_MESSAGES)
    handleApiRequest(
      context,
      authApi.get(`users/tasks/queued/${payload.taskType}`, {
        params: { page: payload.page },
      }),
      (data) => {
        context.commit(
          USERS_STORE.MUTATIONS.UPDATE_USERS_QUEUED_TASKS,
          data.queued_tasks
        )
        context.commit(
          USERS_STORE.MUTATIONS.UPDATE_USERS_QUEUED_TASKS_PAGINATION,
          data.pagination
        )
      }
    )
  },
}
