import type { ActionContext, ActionTree } from 'vuex'

import authApi from '@/api/authApi'
import { activateLanguage } from '@/i18n'
import router from '@/router'
import { ROOT_STORE } from '@/store/constants'
import type { IRootActions, IRootState } from '@/store/modules/root/types'
import { handleApiRequest } from '@/store/request'
import type { TAppConfigForm } from '@/types/application'
import type { TLanguage } from '@/types/locales'
import { handleError } from '@/utils'

export const actions: ActionTree<IRootState, IRootState> & IRootActions = {
  [ROOT_STORE.ACTIONS.GET_APPLICATION_CONFIG](
    context: ActionContext<IRootState, IRootState>
  ): void {
    context.commit(ROOT_STORE.MUTATIONS.EMPTY_ERROR_MESSAGES)
    context.commit(ROOT_STORE.MUTATIONS.UPDATE_APPLICATION_LOADING, true)
    handleApiRequest(context, authApi.get('config'), (data) => {
      context.commit(ROOT_STORE.MUTATIONS.UPDATE_APPLICATION_CONFIG, data.data)
    }).finally(() =>
      context.commit(ROOT_STORE.MUTATIONS.UPDATE_APPLICATION_LOADING, false)
    )
  },
  [ROOT_STORE.ACTIONS.GET_APPLICATION_STATS](
    context: ActionContext<IRootState, IRootState>
  ): void {
    context.commit(ROOT_STORE.MUTATIONS.EMPTY_ERROR_MESSAGES)
    handleApiRequest(context, authApi.get('stats/all'), (data) => {
      context.commit(ROOT_STORE.MUTATIONS.UPDATE_APPLICATION_STATS, data.data)
    })
  },
  [ROOT_STORE.ACTIONS.GET_APPLICATION_PRIVACY_POLICY](
    context: ActionContext<IRootState, IRootState>
  ): void {
    context.commit(ROOT_STORE.MUTATIONS.EMPTY_ERROR_MESSAGES)
    handleApiRequest(context, authApi.get('config'), (data) => {
      context.commit(
        ROOT_STORE.MUTATIONS.UPDATE_APPLICATION_PRIVACY_POLICY,
        data.data
      )
    })
  },
  [ROOT_STORE.ACTIONS.UPDATE_APPLICATION_CONFIG](
    context: ActionContext<IRootState, IRootState>,
    payload: TAppConfigForm
  ): void {
    context.commit(ROOT_STORE.MUTATIONS.EMPTY_ERROR_MESSAGES)
    handleApiRequest(context, authApi.patch('config', payload), (data) => {
      context.commit(ROOT_STORE.MUTATIONS.UPDATE_APPLICATION_CONFIG, data.data)
      router.push('/admin/application')
    })
  },
  [ROOT_STORE.ACTIONS.UPDATE_APPLICATION_LANGUAGE](
    context: ActionContext<IRootState, IRootState>,
    language: TLanguage
  ): Promise<void> {
    return activateLanguage(language)
      .then((activated) => {
        if (!activated) return
        document.querySelector('html')?.setAttribute('lang', language)
        context.commit(ROOT_STORE.MUTATIONS.UPDATE_LANG, language)
      })
      .catch((error) => handleError(context, error))
  },
}
