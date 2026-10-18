<template>
  <div class="view migration-view">
    <div class="container">
      <header>
        <router-link class="back-link" to="/">← Your feed</router-link>
        <p class="eyebrow">CONNECTED TO YOUR TRAINING</p>
        <h1>Imports &amp; data</h1>
        <p>Import your workout history and manage your data.</p>
        <nav class="data-shortcuts" aria-label="Data settings">
          <router-link class="r-secondary" to="/profile/edit/preferences"
            >Units & privacy</router-link
          ><router-link class="r-secondary" to="/profile/account"
            >Account export</router-link
          >
        </nav>
      </header>
      <nav class="source-tabs" aria-label="Import source">
        <button :aria-pressed="source === 'health'" @click="source = 'health'">
          <RintIcon name="watch" />Apple Health & Watch
        </button>
        <button :aria-pressed="source === 'strava'" @click="source = 'strava'">
          <RintIcon name="upload" />Strava export
        </button>
      </nav>
      <section v-if="source === 'health'" class="health-intro">
        <div class="health-visual" aria-hidden="true">
          <div class="health-orbit"><RintIcon name="heart" /></div>
          <span>Your Watch.<br />Your history.</span>
          <div class="health-pills">
            <span>Routes</span><span>Heart rate</span><span>Device laps</span>
          </div>
        </div>
        <div class="health-steps">
          <span class="source-label">WITH THE RINT IPHONE APP</span>
          <a class="r-primary" href="rint://health">Open Rint on iPhone</a>
          <h2>Connect Apple Health</h2>
          <p>
            Bring in past workouts and keep new ones in sync. All available
            charts and exports stay free.
          </p>
          <ol class="setup-steps">
            <li>
              <span>1</span>
              <div>
                <strong>Choose your history</strong
                ><small
                  >Open You → Imports & data → Apple Health in Rint on
                  iPhone.</small
                >
              </div>
            </li>
            <li>
              <span>2</span>
              <div>
                <strong>You choose what to share</strong
                ><small
                  >Allow workout and sensor access in Apple Health. Imports
                  start private.</small
                >
              </div>
            </li>
            <li>
              <span>3</span>
              <div>
                <strong>Make it automatic</strong
                ><small
                  >Import your history, review possible matches, then turn on
                  automatic sync.</small
                >
              </div>
            </li>
          </ol>
          <p class="device-note">
            <RintIcon name="watch" />Apple Health access runs in the native
            iPhone app.
          </p>
        </div>
      </section>
      <section v-if="source === 'strava'" class="migration-panel upload-panel">
        <span class="source-label">STEP 01 · YOUR ORIGINAL RECORDINGS</span>
        <h2>Import your Strava archive</h2>
        <p>
          Upload your Strava account ZIP to review activities, photos and
          privacy before importing.
        </p>
        <label class="file-picker"
          ><RintIcon name="upload" /><strong>Choose your account export</strong
          ><span>ZIP · Original FIT, GPX & TCX recordings</span
          ><input
            type="file"
            accept=".zip,application/zip"
            :disabled="busy"
            @change="preview"
        /></label>
        <details>
          <summary>Where do I get my export?</summary>
          <p>
            In Strava: Settings → My Account → Download account → Request
            download. Upload the ZIP when it arrives.
            <a
              href="https://support.strava.com/en-us/articles/15401919-how-do-i-export-my-strava-data"
              target="_blank"
              rel="noopener noreferrer"
              >Strava’s export instructions ↗</a
            >
          </p>
        </details>
        <p role="status" v-if="uploading">
          Uploading {{ uploadProgress }}% · keep this page open.
        </p>
        <progress
          v-if="uploading"
          :value="uploadProgress"
          max="100"
          aria-label="Upload progress"
        />
        <p class="error" role="alert" v-if="error">{{ error }}</p>
      </section>
      <div class="ownership-note">
        <RintIcon name="shield" />
        <div>
          <strong>Your data stays yours.</strong>
          <p>
            Private imports. Duplicate checks. Progress you can resume. No
            subscription for your metrics.
          </p>
        </div>
      </div>
      <section
        v-if="source === 'strava' && batches.length && !batch"
        class="migration-panel"
      >
        <h2>Pick up where you left off</h2>
        <button v-for="saved in batches" :key="saved.id" @click="batch = saved">
          {{ saved.completed }} / {{ saved.total }} activities ·
          {{ saved.id.slice(0, 8) }}
        </button>
      </section>
      <section v-if="source === 'strava' && batch" class="migration-panel">
        <h2>Review your activities</h2>
        <p>
          Your route stays private. Photos have location metadata removed.
          Choose who can see the imported activities and their analysis.
        </p>
        <label
          >Activity visibility<select v-model="visibility" :disabled="running">
            <option value="private">Only me (recommended)</option>
            <option value="followers_only">My followers</option>
            <option value="public">Everyone</option>
          </select></label
        >
        <label v-for="type in importSports" :key="type"
          >{{ type }} →<select
            v-model="sportMappings[type]"
            :disabled="running"
          >
            <option value="">Match automatically</option>
            <option v-for="sport in sports" :key="sport.id" :value="sport.id">
              {{ sport.label }}
            </option>
          </select></label
        >
        <div class="import-actions">
          <button
            class="primary"
            :disabled="busy || pending === 0"
            @click="run(false)"
          >
            {{ running ? 'Importing…' : 'Import / resume' }}</button
          ><button v-if="running" @click="stop = true">
            Pause after this activity group</button
          ><button v-if="failed && !busy" @click="run(true)">
            Retry {{ failed }} failed activities
          </button>
        </div>
        <progress
          :value="batch.completed"
          :max="batch.total"
          :aria-label="`${batch.completed} of ${batch.total} processed`"
        />
        <p role="status">
          {{ batch.completed }} / {{ batch.total }} processed ·
          {{ imported }} imported · {{ duplicates }} duplicates ·
          {{ failed }} need attention
        </p>
        <p v-if="!pending && !failed" class="success">
          Your history is ready.
          <router-link to="/">Go to your feed →</router-link>
        </p>
        <ol class="import-list">
          <li v-for="item in batch.items" :key="item.index">
            <div>
              <router-link
                v-if="item.workout_id"
                :to="`/workouts/${item.workout_id}`"
                >{{ item.title }}</router-link
              ><strong v-else>{{ item.title }}</strong
              ><small
                >{{ item.sport }} · {{ item.date }} ·
                {{ item.photos.length }} photos</small
              >
              <p v-if="item.error" class="error">{{ item.error }}</p>
              <p v-for="warning in item.warnings" :key="warning">
                {{ warning }}
              </p>
            </div>
            <span :class="item.status">{{ item.status }}</span>
          </li>
        </ol>
        <button :disabled="busy" @click="discard">
          Remove stored migration ZIP
        </button>
        <p class="hint">
          Removing the ZIP clears this migration’s progress. Imported activities
          and their original recordings remain in your account.
        </p>
      </section>
    </div>
  </div>
</template>
<script setup lang="ts">
  import { computed, onMounted, ref, watch } from 'vue'
  import { useRoute } from 'vue-router'

  import authApi from '@/api/authApi'
  import RintIcon from '@/components/Rint/RintIcon.vue'
  import useSports from '@/composables/useSports'
  import type { ImportBatch } from '@/types/rint'
  const { sports } = useSports()
  const route = useRoute()
  const source = ref(route.query.source === 'strava' ? 'strava' : 'health')
  const batch = ref<ImportBatch | null>(null),
    batches = ref<ImportBatch[]>([])
  const uploading = ref(false),
    running = ref(false),
    stop = ref(false),
    error = ref(''),
    uploadProgress = ref(0)
  const visibility = ref('private'),
    sportMappings = ref<Record<string, number | string>>({})
  const importSports = computed(() => [
    ...new Set(batch.value?.items.map((i) => i.sport) || []),
  ])
  watch(
    () => batch.value?.id,
    () => {
      visibility.value = batch.value?.visibility || 'private'
      sportMappings.value = Object.fromEntries(
        importSports.value.map((type) => [type, ''])
      )
    }
  )
  const busy = computed(() => uploading.value || running.value)
  const count = (status: string) =>
    computed(
      () => batch.value?.items.filter((i) => i.status === status).length || 0
    )
  const pending = count('pending'),
    imported = count('imported'),
    duplicates = count('duplicate'),
    failed = count('error')
  function explain(e: unknown) {
    return (
      (e as { response?: { data?: { message?: string } } }).response?.data
        ?.message ||
      'Connection interrupted. Your progress is saved; reconnect and resume.'
    )
  }
  onMounted(async () => {
    try {
      batches.value = (await authApi.get('rint/imports')).data.data
    } catch (e) {
      error.value = explain(e)
    }
  })
  async function preview(event: Event) {
    const file = (event.target as HTMLInputElement).files?.[0]
    if (!file) return
    uploading.value = true
    error.value = ''
    uploadProgress.value = 0
    const form = new FormData()
    form.append('file', file)
    try {
      batch.value = (
        await authApi.post('rint/imports', form, {
          onUploadProgress: (e) => {
            uploadProgress.value = Math.round((e.progress || 0) * 100)
          },
        })
      ).data.data
    } catch (e) {
      error.value = explain(e)
    } finally {
      uploading.value = false
    }
  }
  async function run(retry: boolean) {
    if (!batch.value) return
    const batchId = batch.value.id
    running.value = true
    stop.value = false
    error.value = ''
    try {
      do {
        batch.value = (
          await authApi.post(`rint/imports/${batchId}`, {
            visibility: visibility.value,
            sport_mappings: sportMappings.value,
            retry_errors: retry,
          })
        ).data.data
        retry = false
      } while (!stop.value && pending.value > 0)
    } catch (e) {
      error.value = explain(e)
    } finally {
      running.value = false
    }
  }
  async function discard() {
    if (!batch.value) return
    try {
      await authApi.delete(`rint/imports/${batch.value.id}`)
      batch.value = null
      batches.value = (await authApi.get('rint/imports')).data.data
    } catch (e) {
      error.value = explain(e)
    }
  }
</script>
<style scoped>
  .migration-view {
    color: var(--r-ink);
    min-height: 85vh;
  }
  .container {
    display: block;
    width: 100%;
    box-sizing: border-box;
    max-width: 1020px;
    margin: auto;
    padding: 28px;
  }
  header {
    max-width: 700px;
    margin: 0 0 32px;
  }
  .back-link {
    display: inline-flex;
    min-height: 44px;
    align-items: center;
    color: var(--r-muted);
    font-size: 12px;
    text-decoration: none;
  }
  h1 {
    font-size: clamp(30px, 4vw, 48px);
    line-height: 1.08;
    letter-spacing: -1.8px;
    margin: 14px 0 18px;
  }
  h2 {
    font-size: 28px;
    line-height: 1.15;
    letter-spacing: -0.8px;
    margin: 16px 0;
  }
  p {
    font-size: 14px;
    line-height: 1.7;
    color: var(--r-muted);
  }
  .eyebrow,
  .source-label {
    letter-spacing: 0.12em;
    font-size: 10px;
    font-weight: 750;
    color: var(--r-muted);
  }
  .source-tabs {
    display: flex;
    gap: 12px;
    margin-bottom: 28px;
  }
  .source-tabs button {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    padding: 14px 22px;
    min-height: 52px;
    border: 1px solid var(--r-line);
    border-radius: 100px;
    color: var(--r-muted);
    background: var(--r-surface);
    font-size: 13px;
    font-weight: 650;
  }
  .source-tabs button[aria-pressed='true'] {
    background: var(--r-ink);
    color: var(--r-paper);
    border-color: var(--r-ink);
  }
  .health-intro {
    display: grid;
    grid-template-columns: 40% 60%;
    border: 1px solid var(--r-line);
    border-radius: 24px;
    overflow: hidden;
    background: var(--r-surface);
  }
  .health-visual {
    background: #252c20;
    color: #f5f8eb;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 36px 24px;
    gap: 28px;
  }
  .health-orbit {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 124px;
    height: 124px;
    border: 1px solid #d4f36b44;
    border-radius: 50%;
    box-shadow:
      0 0 0 16px #d4f36b09,
      0 0 0 32px #d4f36b05;
  }
  .health-orbit svg {
    width: 50px;
    height: 50px;
    color: #d4f36b;
    stroke-width: 1.3;
  }
  .health-visual > span {
    font-size: 28px;
    font-weight: 600;
    line-height: 1.15;
    letter-spacing: -1px;
    text-align: center;
  }
  .health-pills {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 6px;
  }
  .health-pills span {
    font-size: 9px;
    padding: 8px 12px;
    border: 1px solid #56604c;
    border-radius: 100px;
    color: #d5dccb;
  }
  .health-steps {
    padding: 36px;
  }
  .health-steps > p {
    font-size: 13px;
  }
  .setup-steps {
    list-style: none;
    padding: 0;
    margin: 26px 0;
  }
  .setup-steps li {
    display: flex;
    gap: 14px;
    align-items: start;
    margin: 22px 0;
    border: 0;
    padding: 0;
  }
  .setup-steps li > span {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background: var(--r-soft);
    font-size: 11px;
    flex-shrink: 0;
  }
  .setup-steps strong {
    font-size: 13px;
  }
  .setup-steps small {
    display: block;
    margin-top: 5px;
    font-size: 11px;
    color: var(--r-muted);
    line-height: 1.7;
  }
  .device-note {
    display: flex;
    gap: 10px;
    align-items: center;
    border-top: 1px solid var(--r-line);
    padding-top: 18px;
    font-size: 11px !important;
  }
  .ownership-note {
    display: flex;
    gap: 14px;
    margin: 24px 4px;
    align-items: start;
  }
  .ownership-note > svg {
    color: var(--r-action);
  }
  .ownership-note strong {
    font-size: 12px;
  }
  .ownership-note p {
    font-size: 11px;
    margin: 6px 0;
  }
  .migration-panel {
    background: var(--r-surface);
    border: 1px solid var(--r-line);
    border-radius: 20px;
    padding: 28px;
    margin: 24px 0;
  }
  .upload-panel {
    padding: 36px;
  }
  .file-picker {
    display: flex;
    align-items: center;
    flex-direction: column;
    gap: 14px;
    background: var(--r-soft);
    padding: 32px 20px;
    border: 1px dashed var(--r-muted);
    border-radius: 16px;
    text-align: center;
  }
  .file-picker > svg {
    width: 30px;
    height: 30px;
    color: var(--r-action);
  }
  .file-picker span {
    font-size: 11px;
    color: var(--r-muted);
  }
  .file-picker input {
    font-size: 12px;
    max-width: 100%;
  }
  label {
    display: block;
    margin: 18px 0;
    font-size: 12px;
    font-weight: 600;
    color: var(--r-muted);
  }
  input,
  select {
    box-sizing: border-box;
    display: block;
    width: 100%;
    max-width: 480px;
    margin-top: 8px;
    padding: 12px;
    min-height: 44px;
    border: 1px solid var(--r-line);
    border-radius: 10px;
    background: var(--r-surface);
    color: var(--r-ink);
  }
  button {
    padding: 12px 18px;
    margin: 4px 8px 4px 0;
    border: 1px solid var(--r-line);
    border-radius: 100px;
    background: var(--r-surface);
    color: var(--r-ink);
    min-height: 44px;
    cursor: pointer;
    font-size: 12px;
  }
  button.primary {
    background: var(--r-accent);
    color: #202719;
    border: 0;
    font-weight: 700;
  }
  button:disabled {
    opacity: 0.5;
  }
  progress {
    width: 100%;
    height: 10px;
    accent-color: var(--r-action);
    margin-top: 18px;
  }
  .import-list {
    padding: 0;
    list-style: none;
    max-height: 500px;
    overflow: auto;
  }
  .import-list li {
    display: flex;
    justify-content: space-between;
    gap: 16px;
    border-top: 1px solid var(--r-line);
    padding: 18px 0;
    font-size: 13px;
  }
  .import-list small {
    display: block;
    color: var(--r-muted);
    font-size: 11px;
    margin-top: 6px;
  }
  .import-list li > span {
    border-radius: 100px;
    padding: 5px 10px;
    font-size: 10px;
    background: var(--r-soft);
    height: max-content;
  }
  .error {
    color: var(--r-heart);
  }
  .success {
    color: var(--r-action);
  }
  .hint {
    font-size: 11px;
    color: var(--r-muted);
  }
  a {
    color: var(--r-action);
  }
  details {
    margin-top: 24px;
  }
  summary {
    cursor: pointer;
    min-height: 44px;
    font-size: 12px;
  }
  @media (max-width: 700px) {
    .container {
      padding: 16px;
    }
    header {
      margin-bottom: 24px;
    }
    h1 {
      font-size: 34px;
      letter-spacing: -1.3px;
      max-width: 310px;
    }
    header > p:last-child {
      font-size: 12px;
    }
    .source-tabs {
      gap: 8px;
      margin-bottom: 20px;
    }
    .source-tabs button {
      font-size: 11px;
      padding: 12px;
      flex: 1;
      margin: 0;
      gap: 7px;
    }
    .source-tabs svg {
      width: 17px;
      height: 17px;
    }
    .health-intro {
      display: flex;
      flex-direction: column;
    }
    .health-visual {
      padding: 24px;
      gap: 16px;
      flex-direction: row;
      flex-wrap: wrap;
    }
    .health-orbit {
      width: 58px;
      height: 58px;
      box-shadow: none;
    }
    .health-orbit svg {
      width: 26px;
      height: 26px;
    }
    .health-visual > span {
      font-size: 22px;
      text-align: left;
    }
    .health-pills {
      width: 100%;
    }
    .health-steps {
      padding: 24px;
    }
    .health-steps h2 {
      font-size: 25px;
    }
    .setup-steps {
      margin: 20px 0;
    }
    .migration-panel,
    .upload-panel {
      padding: 24px;
    }
    .upload-panel h2 {
      font-size: 25px;
    }
    .eyebrow {
      font-size: 9px;
    }
  }
</style>

<style scoped>
  .data-shortcuts {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 18px;
  }
  .health-steps > .r-primary {
    margin: 14px 0;
  }
  .migration-view header .eyebrow {
    margin-top: 20px;
  }
</style>
