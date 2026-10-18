import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import RelationshipDetail from '@/components/Notifications/RelationshipDetail.vue'
import type { INotification } from '@/types/notifications'
import type { IAuthUserProfile } from '@/types/user'

const { dispatch } = vi.hoisted(() => ({ dispatch: vi.fn() }))
vi.mock('@/use/useStore', () => ({ useStore: () => ({ dispatch }) }))

function request() {
  return mount(RelationshipDetail, {
    props: {
      authUser: { username: 'viewer' } as IAuthUserProfile,
      notification: {
        type: 'follow_request',
        from: { username: 'friend' },
      } as INotification,
    },
    global: {
      mocks: { $t: (key: string) => key },
      stubs: {
        UserPicture: true,
        UserRelationshipActions: true,
        RouterLink: true,
      },
    },
  })
}

describe('follow request completion', () => {
  beforeEach(() => dispatch.mockReset())
  it('waits for acceptance before refreshing the inbox and prevents repeated clicks', async () => {
    let complete!: (accepted: boolean) => void
    dispatch.mockReturnValue(
      new Promise<boolean>((resolve) => {
        complete = resolve
      })
    )
    const view = request()
    await view.findAll('button')[0].trigger('click')
    expect(view.emitted('updatedUserRelationship')).toBeUndefined()
    expect(
      view
        .findAll('button')
        .every((button) => button.attributes('disabled') !== undefined)
    ).toBe(true)
    complete(true)
    await flushPromises()
    expect(view.emitted('updatedUserRelationship')).toHaveLength(1)
    expect(view.findAll('button')[0].attributes('disabled')).toBeUndefined()
  })
  it('keeps the request available when acceptance fails', async () => {
    dispatch.mockResolvedValue(false)
    const view = request()
    await view.findAll('button')[0].trigger('click')
    await flushPromises()
    expect(view.emitted('updatedUserRelationship')).toBeUndefined()
    expect(view.findAll('button')[0].attributes('disabled')).toBeUndefined()
  })
})
