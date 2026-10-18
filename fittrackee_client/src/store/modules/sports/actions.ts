import type { ActionContext, ActionTree } from 'vuex'

import authApi from '@/api/authApi'
import { AUTH_USER_STORE, ROOT_STORE, SPORTS_STORE } from '@/store/constants'
import type { IRootState } from '@/store/modules/root/types'
import type { ISportsActions, ISportsState } from '@/store/modules/sports/types'
import { handleApiRequest } from '@/store/request'
import type { ISportPayload } from '@/types/sports'

export const actions: ActionTree<ISportsState, IRootState> & ISportsActions = {
  [SPORTS_STORE.ACTIONS.GET_SPORTS](
    context: ActionContext<ISportsState, IRootState>,
    checkWorkouts: boolean
  ): void {
    context.commit(ROOT_STORE.MUTATIONS.EMPTY_ERROR_MESSAGES)
    handleApiRequest(
      context,
      authApi.get(`sports${checkWorkouts ? '?check_workouts=true' : ''}`),
      (data) => {
        context.commit(SPORTS_STORE.MUTATIONS.SET_SPORTS, data.data.sports)
        context.commit(AUTH_USER_STORE.MUTATIONS.UPDATE_USER_LOADING, false)
      }
    )
  },
  [SPORTS_STORE.ACTIONS.UPDATE_SPORTS](
    context: ActionContext<ISportsState, IRootState>,
    payload: ISportPayload
  ): void {
    context.commit(ROOT_STORE.MUTATIONS.EMPTY_ERROR_MESSAGES)
    handleApiRequest(
      context,
      authApi.patch(`sports/${payload.id}`, { is_active: payload.isActive }),
      () => {
        context.dispatch(SPORTS_STORE.ACTIONS.GET_SPORTS)
      }
    )
  },
}
