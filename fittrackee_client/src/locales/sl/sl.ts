import type { DefineLocaleMessage } from 'vue-i18n'

import { messagesFromSections } from '../messages'

export default messagesFromSections(
  import.meta.glob<DefineLocaleMessage>('./*.json', {
    eager: true,
    import: 'default',
  })
)
