import type { AxiosResponse } from 'axios'

import { handleError } from '@/utils'

/** Shared response contract; each action retains its own state and loading flow. */
export const handleApiRequest = <T extends { status?: string }>(
  context: Parameters<typeof handleError>[0],
  request: Promise<AxiosResponse<T>>,
  onSuccess: (data: T) => void,
  expectedStatus = 'success'
): Promise<void> =>
  request
    .then(({ data }) => {
      if (data.status === expectedStatus) {
        return onSuccess(data)
      }
      handleError(context, null)
    })
    .catch((error) => handleError(context, error))
