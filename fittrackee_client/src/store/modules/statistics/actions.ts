import type { ActionContext, ActionTree } from 'vuex'

import authApi from '@/api/authApi'
import { STATS_STORE, ROOT_STORE } from '@/store/constants'
import type { IRootState } from '@/store/modules/root/types'
import type {
  IStatisticsActions,
  IStatisticsState,
} from '@/store/modules/statistics/types'
import { handleApiRequest } from '@/store/request'
import type {
  IUserSportStatisticsPayload,
  IUserStatisticsPayload,
} from '@/types/statistics'

export const actions: ActionTree<IStatisticsState, IRootState> &
  IStatisticsActions = {
  [STATS_STORE.ACTIONS.GET_USER_STATS](
    context: ActionContext<IStatisticsState, IRootState>,
    payload: IUserStatisticsPayload
  ): void {
    context.commit(ROOT_STORE.MUTATIONS.EMPTY_ERROR_MESSAGES)
    handleApiRequest(
      context,
      authApi.get(`stats/${payload.username}/by_time`, {
        params: payload.params,
      }),
      (data) => {
        context.commit(
          STATS_STORE.MUTATIONS.UPDATE_USER_STATS,
          data.data.statistics
        )
      }
    )
  },
  [STATS_STORE.ACTIONS.GET_USER_SPORT_STATS](
    context: ActionContext<IStatisticsState, IRootState>,
    payload: IUserSportStatisticsPayload
  ): void {
    context.commit(ROOT_STORE.MUTATIONS.EMPTY_ERROR_MESSAGES)
    context.commit(STATS_STORE.MUTATIONS.UPDATE_STATS_LOADING, true)
    handleApiRequest(
      context,
      authApi.get(`stats/${payload.username}/by_sport`, {
        params: { sport_id: payload.sportId },
      }),
      (data) => {
        context.commit(
          STATS_STORE.MUTATIONS.UPDATE_USER_SPORT_STATS,
          data.data.statistics
        )
        context.commit(
          STATS_STORE.MUTATIONS.UPDATE_TOTAL_WORKOUTS,
          data.data.total_workouts
        )
      }
    ).finally(() =>
      context.commit(STATS_STORE.MUTATIONS.UPDATE_STATS_LOADING, false)
    )
  },
}
