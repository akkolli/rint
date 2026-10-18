import type { ActionContext, ActionTree } from 'vuex'

import authApi from '@/api/authApi'
import router from '@/router'
import {
  AUTH_USER_STORE,
  ROOT_STORE,
  EQUIPMENTS_STORE,
  SPORTS_STORE,
} from '@/store/constants'
import type {
  IEquipmentsActions,
  IEquipmentTypesState,
} from '@/store/modules/equipments/types'
import type { IRootState } from '@/store/modules/root/types'
import { handleApiRequest } from '@/store/request'
import type {
  IAddEquipmentPayload,
  IDeleteEquipmentPayload,
  IEquipmentTypePayload,
  IPatchEquipmentPayload,
} from '@/types/equipments'
import { handleError } from '@/utils'

export const actions: ActionTree<IEquipmentTypesState, IRootState> &
  IEquipmentsActions = {
  [EQUIPMENTS_STORE.ACTIONS.ADD_EQUIPMENT](
    context: ActionContext<IEquipmentTypesState, IRootState>,
    payload: IAddEquipmentPayload
  ): void {
    context.commit(ROOT_STORE.MUTATIONS.EMPTY_ERROR_MESSAGES)
    handleApiRequest(
      context,
      authApi.post('equipments', {
        description: payload.description,
        equipment_type_id: payload.equipmentTypeId,
        label: payload.label,
        default_for_sport_ids: payload.defaultForSportIds,
        visibility: payload.visibility,
      }),
      (data) => {
        if (data.data.equipments.length > 0) {
          const equipment = data.data.equipments[0]
          context.commit(EQUIPMENTS_STORE.MUTATIONS.ADD_EQUIPMENT, equipment)
          router.push(`/profile/equipments/${equipment.id}`)
        }
        context.dispatch(SPORTS_STORE.ACTIONS.GET_SPORTS)
        context.commit(AUTH_USER_STORE.MUTATIONS.UPDATE_USER_LOADING, false)
      },
      'created'
    )
  },
  [EQUIPMENTS_STORE.ACTIONS.DELETE_EQUIPMENT](
    context: ActionContext<IEquipmentTypesState, IRootState>,
    payload: IDeleteEquipmentPayload
  ): void {
    context.commit(ROOT_STORE.MUTATIONS.EMPTY_ERROR_MESSAGES)
    authApi
      .delete(`equipments/${payload.id}${payload.force ? '?force' : ''}`)
      .then(() => {
        context.commit(EQUIPMENTS_STORE.MUTATIONS.REMOVE_EQUIPMENT, payload.id)
        context.dispatch(SPORTS_STORE.ACTIONS.GET_SPORTS)
        router.push('/profile/equipments')
      })
      .catch((error) => handleError(context, error))
  },
  [EQUIPMENTS_STORE.ACTIONS.GET_EQUIPMENT](
    context: ActionContext<IEquipmentTypesState, IRootState>,
    equipmentId: number
  ): void {
    context.commit(ROOT_STORE.MUTATIONS.EMPTY_ERROR_MESSAGES)
    handleApiRequest(
      context,
      authApi.get(`equipments/${equipmentId}`),
      (data) => {
        if (data.data.equipments.length > 0) {
          context.commit(
            EQUIPMENTS_STORE.MUTATIONS.UPDATE_EQUIPMENT,
            data.data.equipments[0]
          )
        }
      }
    )
  },
  [EQUIPMENTS_STORE.ACTIONS.GET_EQUIPMENTS](
    context: ActionContext<IEquipmentTypesState, IRootState>
  ): void {
    context.commit(ROOT_STORE.MUTATIONS.EMPTY_ERROR_MESSAGES)
    handleApiRequest(context, authApi.get('equipments'), (data) => {
      context.commit(
        EQUIPMENTS_STORE.MUTATIONS.SET_EQUIPMENTS,
        data.data.equipments
      )
    })
  },
  [EQUIPMENTS_STORE.ACTIONS.GET_EQUIPMENT_TYPES](
    context: ActionContext<IEquipmentTypesState, IRootState>
  ): void {
    context.commit(ROOT_STORE.MUTATIONS.EMPTY_ERROR_MESSAGES)
    handleApiRequest(context, authApi.get('equipment-types'), (data) => {
      context.commit(
        EQUIPMENTS_STORE.MUTATIONS.SET_EQUIPMENT_TYPES,
        data.data.equipment_types
      )
      context.commit(AUTH_USER_STORE.MUTATIONS.UPDATE_USER_LOADING, false)
    })
  },
  [EQUIPMENTS_STORE.ACTIONS.REFRESH_EQUIPMENT](
    context: ActionContext<IEquipmentTypesState, IRootState>,
    equipmentId: string
  ): void {
    context.commit(ROOT_STORE.MUTATIONS.EMPTY_ERROR_MESSAGES)
    context.commit(EQUIPMENTS_STORE.MUTATIONS.SET_LOADING, true)
    handleApiRequest(
      context,
      authApi.post(`equipments/${equipmentId}/refresh`),
      (data) => {
        if (data.data.equipments.length > 0) {
          context.commit(
            EQUIPMENTS_STORE.MUTATIONS.UPDATE_EQUIPMENT,
            data.data.equipments[0]
          )
          router.push(`/profile/equipments/${equipmentId}`)
        }
      }
    ).finally(() =>
      context.commit(EQUIPMENTS_STORE.MUTATIONS.SET_LOADING, false)
    )
  },
  [EQUIPMENTS_STORE.ACTIONS.UPDATE_EQUIPMENT](
    context: ActionContext<IEquipmentTypesState, IRootState>,
    payload: IPatchEquipmentPayload
  ): void {
    context.commit(ROOT_STORE.MUTATIONS.EMPTY_ERROR_MESSAGES)
    context.commit(EQUIPMENTS_STORE.MUTATIONS.SET_LOADING, true)
    handleApiRequest(
      context,
      authApi.patch(`equipments/${payload.id}`, {
        description: payload.description,
        equipment_type_id: payload.equipmentTypeId,
        is_active: payload.isActive,
        label: payload.label,
        default_for_sport_ids: payload.defaultForSportIds,
        visibility: payload.visibility,
      }),
      (data) => {
        if (data.data.equipments.length > 0) {
          context.commit(
            EQUIPMENTS_STORE.MUTATIONS.UPDATE_EQUIPMENT,
            data.data.equipments[0]
          )
          context.dispatch(SPORTS_STORE.ACTIONS.GET_SPORTS)
          router.push(`/profile/equipments/${payload.id}`)
        }
      }
    ).finally(() =>
      context.commit(EQUIPMENTS_STORE.MUTATIONS.SET_LOADING, false)
    )
  },
  [EQUIPMENTS_STORE.ACTIONS.UPDATE_EQUIPMENT_TYPE](
    context: ActionContext<IEquipmentTypesState, IRootState>,
    payload: IEquipmentTypePayload
  ): void {
    context.commit(ROOT_STORE.MUTATIONS.EMPTY_ERROR_MESSAGES)
    context.commit(EQUIPMENTS_STORE.MUTATIONS.SET_LOADING, true)
    handleApiRequest(
      context,
      authApi.patch(`equipment-types/${payload.id}`, {
        is_active: payload.isActive,
      }),
      () => {
        context.dispatch(EQUIPMENTS_STORE.ACTIONS.GET_EQUIPMENT_TYPES)
      }
    ).finally(() =>
      context.commit(EQUIPMENTS_STORE.MUTATIONS.SET_LOADING, false)
    )
  },
}
