<template>
  <div
    id="workout-edition"
    class="center-card"
    :class="{
      'center-form': workout && workout.with_file,
      'with-margin': !isCreation,
    }"
  >
    <Card>
      <template #title>{{
        $t(`workouts.${isCreation ? 'ADD' : 'EDIT'}_WORKOUT`)
      }}</template>
      <template #content>
        <div id="workout-form">
          <form :class="{ errors: formErrors }" @submit.prevent="updateWorkout">
            <div class="form-items">
              <div class="form-item-radio" v-if="isCreation">
                <div>
                  <input
                    id="withFile"
                    name="activity-entry"
                    type="radio"
                    :checked="withFile"
                    :disabled="disabled"
                    @change="updateWithFile(true)"
                  />
                  <label for="withFile">Upload a file</label>
                </div>
                <div>
                  <input
                    id="withoutGpx"
                    name="activity-entry"
                    type="radio"
                    :checked="!withFile"
                    :disabled="disabled"
                    @change="updateWithFile(false)"
                  />
                  <label for="withoutGpx"> Add manually </label>
                </div>
              </div>
              <div class="form-item">
                <label for="sport"> {{ $t('workouts.SPORT', 1) }}*: </label>
                <select
                  id="sport"
                  required
                  @invalid="invalidateForm"
                  :disabled="disabled"
                  v-model="workoutForm.sport_id"
                >
                  <option
                    v-for="sport in translatedSports"
                    :value="sport.id"
                    :key="sport.id"
                  >
                    {{ sport.translatedLabel }}
                  </option>
                </select>
              </div>
              <div class="form-item" v-if="isCreation && withFile">
                <label for="workoutFile"> Activity file * </label>
                <input
                  id="workoutFile"
                  name="workoutFile"
                  type="file"
                  accept=".gpx, .fit, .kml, .kmz, .tcx, .zip"
                  :disabled="disabled"
                  required
                  @invalid="invalidateForm"
                  @input="updateFile"
                />
                <details class="file-format-help">
                  <summary>File formats &amp; limits</summary>
                  <div class="files-info-box info-box">
                    <div class="files-help">
                      <div>
                        <strong>{{ $t('workouts.WORKOUT_FILE') }}:</strong>
                        <ul>
                          <li>
                            {{ $t('workouts.MAX_SIZE') }}: {{ fileSizeLimit }}
                          </li>
                          <li>
                            {{ $t('workouts.SUPPORTED_FILE_EXTENSIONS') }}:
                            .gpx, .fit, .kml, .kmz, .tcx
                          </li>
                        </ul>
                      </div>
                      <div>
                        <strong>{{ $t('workouts.ZIP_ARCHIVE') }}:</strong>
                        <ul>
                          <li>
                            {{ $t('workouts.MAX_SIZE') }}: {{ zipSizeLimit }}
                          </li>
                          <li>
                            {{ $t('workouts.MAX_FILES') }}:
                            {{ fileLimitImport }}
                          </li>
                          <li v-if="asyncUploadEnabled">
                            {{ $t('workouts.MAX_SYNC_FILES_IN_ZIP') }}:
                            {{ fileSyncLimitImport }}
                          </li>
                        </ul>
                      </div>
                    </div>
                    <div
                      class="weather-info"
                      v-if="
                        asyncUploadEnabled &&
                        appConfig.weather_provider !== null
                      "
                    >
                      <i class="fa fa-info-circle" aria-hidden="true" />
                      {{ $t('workouts.NO_WEATHER_WITH_ASYNCHRONOUS_UPLOAD') }}
                    </div>
                  </div>
                </details>
              </div>
              <div class="form-item">
                <label for="title">
                  {{ $t('workouts.TITLE') }}{{ isCreation ? '' : '*' }}:
                </label>
                <input
                  id="title"
                  name="title"
                  type="text"
                  :required="!isCreation"
                  @invalid="invalidateForm"
                  :disabled="disabled"
                  v-model="workoutForm.title"
                  maxlength="255"
                />
                <div class="field-help" v-if="withFile && isCreation">
                  <span class="info-box">
                    <i class="fa fa-info-circle" aria-hidden="true" />
                    {{ $t('workouts.TITLE_FIELD_HELP') }}
                  </span>
                </div>
              </div>
              <div v-if="!withFile">
                <div class="workout-date-duration">
                  <div class="form-item">
                    <label for="workout-date"
                      >{{ $t('workouts.WORKOUT_DATE') }}*:</label
                    >
                    <div class="workout-date-time">
                      <input
                        id="workout-date"
                        name="workout-date"
                        type="date"
                        required
                        @invalid="invalidateForm"
                        :disabled="disabled"
                        v-model="workoutForm.workoutDate"
                      />
                      <label for="workout-time" class="visually-hidden"
                        >Start time</label
                      >
                      <input
                        id="workout-time"
                        name="workout-time"
                        class="workout-time"
                        type="time"
                        required
                        @invalid="invalidateForm"
                        :disabled="disabled"
                        v-model="workoutForm.workoutTime"
                      />
                    </div>
                  </div>
                  <div class="form-item">
                    <label>{{ $t('workouts.DURATION') }}*:</label>
                    <div>
                      <label
                        for="workout-duration-hour"
                        class="visually-hidden"
                      >
                        {{ $t('common.HOURS', 0) }}
                      </label>
                      <input
                        id="workout-duration-hour"
                        name="workout-duration-hour"
                        class="workout-duration"
                        :class="{ errored: isDurationInvalid() }"
                        type="text"
                        inputmode="numeric"
                        placeholder="HH"
                        minlength="1"
                        maxlength="2"
                        pattern="^([0-1]?[0-9]|2[0-3])$"
                        required
                        @invalid="invalidateForm"
                        :disabled="disabled"
                        v-model="workoutForm.workoutDurationHours"
                      />
                      :
                      <label
                        for="workout-duration-minutes"
                        class="visually-hidden"
                      >
                        {{ $t('common.MINUTES', 0) }}
                      </label>
                      <input
                        id="workout-duration-minutes"
                        name="workout-duration-minutes"
                        class="workout-duration"
                        :class="{ errored: isDurationInvalid() }"
                        type="text"
                        inputmode="numeric"
                        pattern="^([0-5][0-9])$"
                        minlength="2"
                        maxlength="2"
                        placeholder="MM"
                        required
                        @invalid="invalidateForm"
                        :disabled="disabled"
                        v-model="workoutForm.workoutDurationMinutes"
                      />
                      :
                      <label
                        for="workout-duration-seconds"
                        class="visually-hidden"
                      >
                        {{ $t('common.SECONDS', 0) }}
                      </label>
                      <input
                        id="workout-duration-seconds"
                        name="workout-duration-seconds"
                        class="workout-duration"
                        :class="{ errored: isDurationInvalid() }"
                        type="text"
                        inputmode="numeric"
                        pattern="^([0-5][0-9])$"
                        minlength="2"
                        maxlength="2"
                        placeholder="SS"
                        required
                        @invalid="invalidateForm"
                        :disabled="disabled"
                        v-model="workoutForm.workoutDurationSeconds"
                      />
                    </div>
                  </div>
                  <div class="form-item">
                    <label for="workout-calories">
                      {{ $t('workouts.CALORIES') }} ({{
                        t(`workouts.UNITS.kcal.UNIT`)
                      }}):
                    </label>
                    <div class="workout-calories">
                      <input
                        id="workout-calories"
                        name="workout-calories"
                        type="number"
                        min="0"
                        @invalid="invalidateForm"
                        :disabled="disabled"
                        v-model="workoutForm.workoutCalories"
                      />
                    </div>
                  </div>
                </div>
                <div class="workout-data">
                  <div class="form-item">
                    <label for="workout-distance">
                      {{ $t('workouts.DISTANCE') }} ({{
                        authUser.imperial_units ? 'mi' : 'km'
                      }})*:
                    </label>
                    <input
                      :class="{ errored: isDistanceInvalid() }"
                      id="workout-distance"
                      name="workout-distance"
                      type="number"
                      max="999.999"
                      min="0"
                      step="0.001"
                      required
                      @invalid="invalidateForm"
                      :disabled="disabled"
                      v-model="workoutForm.workoutDistance"
                    />
                  </div>
                  <div class="form-item">
                    <label for="workout-ascent">
                      {{ $t('workouts.ASCENT') }} ({{
                        authUser.imperial_units ? 'ft' : 'm'
                      }}):
                    </label>
                    <input
                      :class="{ errored: isElevationInvalid() }"
                      id="workout-ascent"
                      name="workout-ascent"
                      type="number"
                      max="99999.999"
                      min="0"
                      step="0.001"
                      @invalid="invalidateForm"
                      :disabled="disabled || withoutElevation"
                      v-model="workoutForm.workoutAscent"
                    />
                  </div>
                  <div class="form-item">
                    <label for="workout-descent">
                      {{ $t('workouts.DESCENT') }} ({{
                        authUser.imperial_units ? 'ft' : 'm'
                      }}):
                    </label>
                    <input
                      :class="{ errored: isElevationInvalid() }"
                      id="workout-descent"
                      name="workout-descent"
                      type="number"
                      max="99999.999"
                      min="0"
                      step="0.001"
                      @invalid="invalidateForm"
                      :disabled="disabled || withoutElevation"
                      v-model="workoutForm.workoutDescent"
                    />
                  </div>
                </div>
              </div>
              <fieldset class="activity-sharing-fields">
                <legend>Who can see this activity?</legend>
                <div class="form-item">
                  <label for="workout_visibility">
                    {{ $t('visibility_levels.WORKOUT_VISIBILITY') }}:
                  </label>
                  <select
                    id="workout_visibility"
                    v-model="workoutForm.workoutVisibility"
                    :disabled="disabled"
                    @change="updateAnalysisMapAndMediaVisibility"
                  >
                    <option
                      v-for="level in visibilityLevels"
                      :value="level"
                      :key="level"
                    >
                      {{ $t(`visibility_levels.LEVELS.${level}`) }}
                    </option>
                  </select>
                </div>
                <div class="form-item" v-if="withFile">
                  <label for="analysis_visibility">
                    {{ $t('visibility_levels.ANALYSIS_VISIBILITY') }}:
                  </label>
                  <select
                    id="analysis_visibility"
                    v-model="workoutForm.analysisVisibility"
                    @change="updateMapVisibility"
                    :disabled="disabled"
                  >
                    <option
                      v-for="level in analysisVisibilityLevels"
                      :value="level"
                      :key="level"
                    >
                      {{ $t(`visibility_levels.LEVELS.${level}`) }}
                    </option>
                  </select>
                </div>
                <div class="form-item" v-if="withFile">
                  <label for="map_visibility">
                    {{ $t('visibility_levels.MAP_VISIBILITY') }}:
                  </label>
                  <select
                    id="map_visibility"
                    v-model="workoutForm.mapVisibility"
                    :disabled="disabled"
                  >
                    <option
                      v-for="level in mapVisibilityLevels"
                      :value="level"
                      :key="level"
                    >
                      {{ $t(`visibility_levels.LEVELS.${level}`) }}
                    </option>
                  </select>
                </div>
                <div class="form-item">
                  <label for="media_visibility">
                    {{ $t('visibility_levels.MEDIA_VISIBILITY') }}:
                  </label>
                  <select
                    id="media_visibility"
                    v-model="workoutForm.mediaVisibility"
                    :disabled="disabled"
                  >
                    <option
                      v-for="level in mediaVisibilityLevels"
                      :value="level"
                      :key="level"
                    >
                      {{ $t(`visibility_levels.LEVELS.${level}`) }}
                    </option>
                  </select>
                </div>
              </fieldset>
              <details class="optional-activity-details" :open="!isCreation">
                <summary>Photos, notes &amp; equipment</summary>
                <div class="form-item" v-if="equipments">
                  <label for="workout-equipment">
                    {{ $t('equipments.EQUIPMENT', 1) }}:
                  </label>
                  <EquipmentMultiSelect
                    :equipment-list="equipmentsForSelect"
                    :disabled="disabled || !selectedSport"
                    :name="'sport-default-equipment'"
                    :existing-equipment-list="existingWorkoutEquipments"
                    @updatedValues="updateSelectedEquipmentPieces"
                  />
                </div>
                <div class="form-item" v-if="isCreation">
                  <label for="description">
                    {{ $t('workouts.DESCRIPTION') }}:
                  </label>
                  <CustomTextArea
                    name="description"
                    :input="workoutForm.description"
                    :disabled="disabled"
                    :charLimit="10000"
                    :rows="5"
                    with-markdown
                    :with-markdown-info="'text'"
                    @updateValue="updateDescription"
                  />
                  <div class="field-help" v-if="withFile && isCreation">
                    <span class="info-box">
                      <i class="fa fa-info-circle" aria-hidden="true" />
                      {{ $t('workouts.DESCRIPTION_FIELD_HELP') }}
                    </span>
                  </div>
                </div>
                <div class="form-item" v-if="isCreation">
                  <label for="notes">
                    {{ $t('workouts.PRIVATE_NOTES') }}:
                  </label>
                  <CustomTextArea
                    name="notes"
                    :charLimit="500"
                    :rows="2"
                    :input="workoutForm.notes"
                    :disabled="disabled"
                    with-markdown
                    :with-markdown-info="'text'"
                    @updateValue="updateNotes"
                  />
                  <div class="field-help" v-if="isCreation">
                    <span class="info-box">
                      <i class="fa fa-info-circle" aria-hidden="true" />
                      {{ $t('workouts.PRIVATE_NOTES_FIELD_HELP') }}
                    </span>
                  </div>
                </div>
                <WorkoutMediaAttachementsUpload
                  :loading="loading"
                  :workout-media-attachments="
                    workout?.media_attachments ? workout.media_attachments : []
                  "
                  :is-archive="isArchive"
                />
              </details>
            </div>
            <ErrorMessage :message="errorMessages" v-if="errorMessages" />
            <div v-if="loading">
              <Loader />
            </div>
            <div v-else class="form-buttons">
              <button class="confirm" type="submit" :disabled="disabled">
                {{ isCreation ? 'Save activity' : $t('buttons.SUBMIT') }}
              </button>
              <button
                class="cancel"
                @click.prevent="onCancel"
                :disabled="disabled"
              >
                {{ $t('buttons.CANCEL') }}
              </button>
            </div>
          </form>
        </div>
      </template>
    </Card>
  </div>
</template>

<script setup lang="ts">
  import { computed, onMounted, reactive, ref, toRefs, watch } from 'vue'
  import type { ComputedRef, Ref } from 'vue'
  import { useI18n } from 'vue-i18n'
  import { useRoute, useRouter } from 'vue-router'

  import EquipmentMultiSelect from '@/components/User/UserEquipments/EquipmentMultiSelect.vue'
  import WorkoutMediaAttachementsUpload from '@/components/Workout/WorkoutMediaAttachementsUpload.vue'
  import useApp from '@/composables/useApp'
  import {
    EQUIPMENTS_STORE,
    ROOT_STORE,
    WORKOUTS_STORE,
  } from '@/store/constants'
  import type {
    IEquipment,
    IEquipmentMultiselectItemsGroup,
  } from '@/types/equipments'
  import type { ICustomTextareaData } from '@/types/forms'
  import type { ISport, ITranslatedSport } from '@/types/sports'
  import type { IAuthUserProfile, TVisibilityLevels } from '@/types/user'
  import type { IWorkout, IWorkoutForm } from '@/types/workouts'
  import { useStore } from '@/use/useStore'
  import { formatWorkoutDate, getDateWithTZ } from '@/utils/dates'
  import {
    getEquipments,
    sortEquipments,
    SPORT_EQUIPMENT_TYPES,
  } from '@/utils/equipments'
  import { getReadableFileSizeAsText } from '@/utils/files'
  import { translateSports, sportsWithoutElevation } from '@/utils/sports'
  import { convertDistance } from '@/utils/units'
  import {
    getAllVisibilityLevels,
    getVisibilityLevels,
    getUpdatedVisibility,
  } from '@/utils/visibility_levels'

  interface Props {
    authUser: IAuthUserProfile
    sports: ISport[]
    isCreation?: boolean
    loading?: boolean
    workout?: IWorkout
  }
  const props = withDefaults(defineProps<Props>(), {
    isCreation: false,
    loading: false,
    workout: () => ({}) as IWorkout,
  })
  const { authUser, workout, isCreation, loading } = toRefs(props)

  const route = useRoute()
  const router = useRouter()
  const store = useStore()
  const { t } = useI18n()

  const { appConfig, errorMessages } = useApp()

  const workoutFile: Ref<File | undefined> = ref(undefined)

  const workoutForm = reactive({
    sport_id: '',
    title: '',
    notes: '',
    workoutDate: '',
    workoutTime: '',
    workoutDurationHours: '',
    workoutDurationMinutes: '',
    workoutDurationSeconds: '',
    workoutDistance: '',
    workoutAscent: '',
    workoutDescent: '',
    equipment_ids: [] as string[],
    description: '',
    mapVisibility: authUser.value.map_visibility,
    analysisVisibility: authUser.value.analysis_visibility,
    workoutVisibility: authUser.value.workouts_visibility,
    mediaVisibility: authUser.value.media_visibility,
    workoutCalories: '',
  })
  const withFile: Ref<boolean> = ref(
    workout.value.id && workout.value.with_file ? true : isCreation.value
  )
  const formErrors: Ref<boolean> = ref(false)
  const payloadErrorMessages: Ref<string[]> = ref([])

  const translatedSports: ComputedRef<ITranslatedSport[]> = computed(() =>
    translateSports(
      props.sports,
      t,
      'is_active_for_user',
      workout.value.id ? [workout.value.sport_id] : []
    )
  )
  const fileSizeLimit: ComputedRef<string> = computed(() =>
    appConfig.value.max_single_file_size
      ? getReadableFileSizeAsText(appConfig.value.max_single_file_size)
      : ''
  )
  const fileLimitImport: ComputedRef<number> = computed(
    () => appConfig.value.file_limit_import
  )
  const fileSyncLimitImport: ComputedRef<number> = computed(
    () => appConfig.value.file_sync_limit_import
  )
  const zipSizeLimit: ComputedRef<string> = computed(() =>
    appConfig.value.max_zip_file_size
      ? getReadableFileSizeAsText(appConfig.value.max_zip_file_size)
      : ''
  )
  const asyncUploadEnabled: ComputedRef<boolean> = computed(
    () =>
      appConfig.value.file_sync_limit_import !=
      appConfig.value.file_limit_import
  )
  const isArchive: ComputedRef<boolean> = computed(
    () =>
      isCreation.value &&
      withFile.value &&
      workoutFile.value !== undefined &&
      workoutFile.value.name.endsWith('.zip')
  )
  const equipments: ComputedRef<IEquipment[]> = computed(
    () => store.getters[EQUIPMENTS_STORE.GETTERS.EQUIPMENTS]
  )
  const selectedSport: ComputedRef<ITranslatedSport | null> = computed(() =>
    workoutForm.sport_id
      ? translatedSports.value.filter((s) => s.id === +workoutForm.sport_id)[0]
      : null
  )
  // eslint-disable-next-line @typescript-eslint/ban-ts-comment
  // @ts-ignore
  const existingWorkoutEquipments: ComputedRef<IEquipment[]> = computed(() =>
    isCreation.value
      ? selectedSport.value?.default_equipments.filter((e) => e.is_active) || []
      : workout.value.equipments.filter((e) =>
          selectedSport.value
            ? (e as IEquipment).equipment_type.label === 'Misc' ||
              SPORT_EQUIPMENT_TYPES[
                (e as IEquipment).equipment_type.label
              ].includes(selectedSport.value.label)
            : []
        )
  )
  const equipmentsForSelect: ComputedRef<IEquipmentMultiselectItemsGroup[]> =
    computed(() =>
      equipments.value
        ? getEquipments(
            equipments.value,
            t,
            isCreation.value ? 'is_active' : 'withIncludedIds',
            selectedSport.value,
            isCreation.value
              ? []
              : // eslint-disable-next-line @typescript-eslint/ban-ts-comment
                // @ts-ignore
                workout.value.equipments.map((e) => e.id)
          )
        : []
    )
  const withoutElevation: ComputedRef<boolean> = computed(() =>
    selectedSport.value?.label
      ? sportsWithoutElevation.includes(selectedSport.value.label)
      : false
  )
  const visibilityLevels: ComputedRef<TVisibilityLevels[]> = computed(() =>
    getAllVisibilityLevels()
  )
  const analysisVisibilityLevels: ComputedRef<TVisibilityLevels[]> = computed(
    () => getVisibilityLevels(workoutForm.workoutVisibility)
  )
  const mapVisibilityLevels: ComputedRef<TVisibilityLevels[]> = computed(() =>
    getVisibilityLevels(workoutForm.analysisVisibility)
  )
  const mediaVisibilityLevels: ComputedRef<TVisibilityLevels[]> = computed(() =>
    getVisibilityLevels(workoutForm.workoutVisibility)
  )
  const disabled: ComputedRef<boolean> = computed(
    () =>
      loading.value ||
      store.getters[WORKOUTS_STORE.GETTERS.WORKOUT_MEDIA_LOADING] === 'new' ||
      store.getters[WORKOUTS_STORE.GETTERS.IS_EDITING_MEDIA]
  )
  const mediaAttachementIds: ComputedRef<string[]> = computed(() =>
    store.getters[WORKOUTS_STORE.GETTERS.WORKOUT_MEDIA_ATTACHMENTS].map(
      (m) => m.id
    )
  )

  function updateNotes(textareaData: ICustomTextareaData) {
    workoutForm.notes = textareaData.value
  }
  function updateDescription(textareaData: ICustomTextareaData) {
    workoutForm.description = textareaData.value
  }
  function updateWithFile(value: boolean) {
    withFile.value = value
    formErrors.value = false
  }
  function updateFile(event: Event) {
    if ((event.target as HTMLInputElement).files) {
      workoutFile.value = (
        (event.target as HTMLInputElement).files as FileList
      )[0]
    }
  }
  function formatWorkoutForm(workout: IWorkout) {
    workoutForm.sport_id = `${workout.sport_id}`
    workoutForm.title = workout.title
    workoutForm.description = workout.description
    workoutForm.notes = workout.notes
    workoutForm.equipment_ids = (workout.equipments as IEquipment[])
      .sort(sortEquipments)
      .map((e) => e.id)
    workoutForm.workoutVisibility = workout.workout_visibility
      ? workout.workout_visibility
      : 'private'
    workoutForm.analysisVisibility = workout.analysis_visibility
      ? workout.analysis_visibility
      : 'private'
    workoutForm.mapVisibility = workout.map_visibility
      ? workout.map_visibility
      : 'private'
    workoutForm.mediaVisibility = workout.media_visibility
      ? workout.media_visibility
      : 'private'
    if (!workout.with_file) {
      const workoutDateTime = formatWorkoutDate(
        getDateWithTZ(workout.workout_date, props.authUser.timezone),
        'yyyy-MM-dd'
      )
      if (workout.duration) {
        const [hours, minutes, seconds] = workout.duration.split(':')
        workoutForm.workoutDurationHours = hours
        workoutForm.workoutDurationMinutes = minutes
        workoutForm.workoutDurationSeconds = seconds
      }
      if (workout.distance) {
        workoutForm.workoutDistance = `${
          authUser.value.imperial_units
            ? convertDistance(workout.distance, 'km', 'mi', 3)
            : parseFloat(workout.distance.toFixed(3))
        }`
      }
      workoutForm.workoutDate = workoutDateTime.workout_date
      workoutForm.workoutTime = workoutDateTime.workout_time
      workoutForm.workoutAscent =
        workout.ascent === null
          ? ''
          : `${
              authUser.value.imperial_units
                ? convertDistance(workout.ascent, 'm', 'ft', 2)
                : parseFloat(workout.ascent.toFixed(2))
            }`
      workoutForm.workoutDescent =
        workout.descent === null
          ? ''
          : `${
              authUser.value.imperial_units
                ? convertDistance(workout.descent, 'm', 'ft', 2)
                : parseFloat(workout.descent.toFixed(2))
            }`
      workoutForm.workoutCalories = workout.calories
        ? `${workout.calories}`
        : ''
    }
  }
  function isDistanceInvalid() {
    return payloadErrorMessages.value.includes('workouts.INVALID_DISTANCE')
  }
  function isDurationInvalid() {
    return payloadErrorMessages.value.includes('workouts.INVALID_DURATION')
  }
  function isElevationInvalid() {
    return payloadErrorMessages.value.includes(
      'workouts.INVALID_ASCENT_OR_DESCENT'
    )
  }
  function formatPayload(payload: IWorkoutForm) {
    payloadErrorMessages.value = []
    payload.duration =
      +workoutForm.workoutDurationHours * 3600 +
      +workoutForm.workoutDurationMinutes * 60 +
      +workoutForm.workoutDurationSeconds
    if (payload.duration <= 0) {
      payloadErrorMessages.value.push('workouts.INVALID_DURATION')
    }
    payload.distance = authUser.value.imperial_units
      ? convertDistance(+workoutForm.workoutDistance, 'mi', 'km', 3)
      : +workoutForm.workoutDistance
    if (payload.distance <= 0) {
      payloadErrorMessages.value.push('workouts.INVALID_DISTANCE')
    }
    payload.workout_date = `${workoutForm.workoutDate} ${workoutForm.workoutTime}`
    payload.ascent =
      workoutForm.workoutAscent === ''
        ? null
        : authUser.value.imperial_units
          ? convertDistance(+workoutForm.workoutAscent, 'ft', 'm', 3)
          : +workoutForm.workoutAscent
    payload.descent =
      workoutForm.workoutDescent === ''
        ? null
        : authUser.value.imperial_units
          ? convertDistance(+workoutForm.workoutDescent, 'ft', 'm', 3)
          : +workoutForm.workoutDescent
    if (
      (payload.ascent !== null && payload.descent === null) ||
      (payload.ascent === null && payload.descent !== null)
    ) {
      payloadErrorMessages.value.push('workouts.INVALID_ASCENT_OR_DESCENT')
    }
    payload.workout_visibility = workoutForm.workoutVisibility
    if (!withFile.value) {
      payload.calories = workoutForm.workoutCalories
        ? +workoutForm.workoutCalories
        : null
    }
  }
  function updateWorkout() {
    const payload: IWorkoutForm = {
      sport_id: +workoutForm.sport_id,
      description: workoutForm.description,
      notes: workoutForm.notes,
      equipment_ids: workoutForm.equipment_ids,
      title: workoutForm.title,
      workout_visibility: workoutForm.workoutVisibility,
      media_attachment_ids: isArchive.value ? [] : mediaAttachementIds.value,
      media_visibility: workoutForm.mediaVisibility,
    }
    if (props.workout.id) {
      if (props.workout.with_file) {
        payload.analysis_visibility = workoutForm.analysisVisibility
        payload.map_visibility = workoutForm.mapVisibility
      } else {
        formatPayload(payload)
      }
      if (payloadErrorMessages.value.length > 0) {
        store.commit(
          ROOT_STORE.MUTATIONS.SET_ERROR_MESSAGES,
          payloadErrorMessages.value
        )
      } else {
        store.dispatch(WORKOUTS_STORE.ACTIONS.EDIT_WORKOUT, {
          workoutId: props.workout.id,
          data: payload,
        })
      }
    } else {
      if (withFile.value) {
        if (!workoutFile.value) {
          const errorMessage = 'workouts.NO_FILE_PROVIDED'
          store.commit(ROOT_STORE.MUTATIONS.SET_ERROR_MESSAGES, errorMessage)
          return
        }
        payload.file = workoutFile.value
        payload.analysis_visibility = workoutForm.analysisVisibility
        payload.map_visibility = workoutForm.mapVisibility
        store.dispatch(WORKOUTS_STORE.ACTIONS.ADD_WORKOUT, payload)
      } else {
        formatPayload(payload)
        if (payloadErrorMessages.value.length > 0) {
          store.commit(
            ROOT_STORE.MUTATIONS.SET_ERROR_MESSAGES,
            payloadErrorMessages.value
          )
        } else {
          store.dispatch(
            WORKOUTS_STORE.ACTIONS.ADD_WORKOUT_WITHOUT_FILE,
            payload
          )
        }
      }
    }
  }
  function onCancel() {
    if (props.workout.id) {
      router.push({
        name: 'Workout',
        params: { workoutId: props.workout.id },
      })
    } else if (window.history.length > 1) {
      router.go(-1)
    } else {
      router.push('/')
    }
  }
  function invalidateForm() {
    formErrors.value = true
  }
  function updateAnalysisMapAndMediaVisibility() {
    workoutForm.analysisVisibility = getUpdatedVisibility(
      workoutForm.analysisVisibility,
      workoutForm.workoutVisibility
    )
    workoutForm.mediaVisibility = getUpdatedVisibility(
      workoutForm.mediaVisibility,
      workoutForm.workoutVisibility
    )
    updateMapVisibility()
  }
  function updateMapVisibility() {
    workoutForm.mapVisibility = getUpdatedVisibility(
      workoutForm.mapVisibility,
      workoutForm.analysisVisibility
    )
  }
  function updateSelectedEquipmentPieces(selectedIds: string[]) {
    workoutForm.equipment_ids = selectedIds
  }

  watch(
    () => props.workout,
    async (
      newWorkout: IWorkout | undefined,
      previousWorkout: IWorkout | undefined
    ) => {
      if (newWorkout !== previousWorkout && newWorkout && newWorkout.id) {
        formatWorkoutForm(newWorkout)
      }
    }
  )
  watch(
    () => selectedSport.value,
    (newSport: ISport | null) => {
      if (isCreation.value) {
        workoutForm.equipment_ids = newSport
          ? newSport.default_equipments.map((e) => e.id)
          : []
      }
    }
  )
  watch(
    () => withoutElevation.value,
    (newValue: boolean) => {
      if (newValue) {
        workoutForm.workoutAscent = ''
        workoutForm.workoutDescent = ''
      }
    }
  )
  watch(
    () => authUser.value,
    (newAuthUser: IAuthUserProfile) => {
      if (newAuthUser && isCreation) {
        workoutForm.workoutVisibility = newAuthUser.workouts_visibility
        workoutForm.analysisVisibility = newAuthUser.analysis_visibility
        workoutForm.mapVisibility = newAuthUser.map_visibility
      }
    }
  )
  watch(
    () => withFile.value,
    async (newValue: boolean) => {
      if (!newValue) {
        workoutFile.value = undefined
      }
    }
  )

  onMounted(() => {
    let element
    if (props.workout.id) {
      formatWorkoutForm(props.workout)
      element = document.getElementById(
        route.hash ? route.hash.replace('#', '') : 'sport'
      )
    }
    element?.focus({ preventScroll: true })
  })
</script>

<style scoped>
  #workout-edition :deep(.card) {
    border-radius: 14px;
    margin: 0;
    background: var(--r-surface);
  }
  #workout-edition :deep(.card-content) {
    padding: 22px;
  }
  #workout-edition #workout-form .form-items label {
    text-transform: none;
    font-size: 13px;
    font-weight: 550;
    line-height: 1.5;
    margin-bottom: 6px;
  }
  #workout-edition #workout-form .form-items input:not([type='radio']),
  #workout-edition #workout-form .form-items select {
    min-height: 44px;
    height: auto;
    padding: 10px 12px;
    border: 1px solid var(--r-line);
    border-radius: 8px;
    box-sizing: border-box;
    font-size: 14px;
    background: var(--r-surface);
    color: var(--r-ink);
  }
  #workout-edition #workout-form .form-items .form-item {
    display: flex;
    flex-direction: column;
    padding: 0;
    margin-bottom: 20px;
  }
  #workout-edition #workout-form .form-items .form-item-radio {
    display: flex;
    gap: 4px;
    padding: 4px;
    background: var(--r-soft);
    border-radius: 10px;
    margin-bottom: 24px;
  }
  .form-item-radio > div {
    flex: 1;
    position: relative;
  }
  #workout-edition #workout-form .form-item-radio input {
    position: absolute;
    opacity: 0;
    width: 1px;
    height: 1px;
  }
  #workout-edition #workout-form .form-item-radio label {
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    min-height: 44px;
    margin: 0;
    border-radius: 8px;
  }
  #workout-edition #workout-form .form-item-radio input:checked + label {
    background: var(--r-surface);
    color: var(--r-ink);
    font-weight: 700;
    box-shadow: 0 1px 3px #16291c0f;
  }
  #workout-edition #workout-form .form-item-radio input:focus-visible + label {
    outline: 3px solid var(--r-violet);
    outline-offset: 2px;
  }
  .workout-date-time {
    display: flex;
    gap: 12px;
  }
  .workout-date-time input {
    min-width: 0;
    flex: 1;
  }
  #workout-edition #workout-form .workout-duration {
    width: 62px;
  }
  .workout-data {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 16px;
  }
  .activity-sharing-fields {
    margin: 4px 0 18px;
    padding: 20px 0 0;
    border: 0;
    border-top: 1px solid var(--r-line);
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0 18px;
  }
  .activity-sharing-fields legend {
    font-size: 15px;
    font-weight: 700;
    padding: 0 10px 0 0;
  }
  .file-format-help summary,
  .optional-activity-details > summary {
    min-height: 44px;
    display: flex;
    align-items: center;
    gap: 12px;
    cursor: pointer;
    color: var(--r-muted);
    font-size: 13px;
  }
  .file-format-help summary::after,
  .optional-activity-details > summary::after {
    content: '+';
    margin-left: auto;
    font-size: 20px;
  }
  .file-format-help[open] summary::after,
  .optional-activity-details[open] > summary::after {
    content: '−';
  }
  .optional-activity-details {
    border-top: 1px solid var(--r-line);
    padding-top: 4px;
  }
  .optional-activity-details > summary {
    font-weight: 650;
    color: var(--r-ink);
    margin-bottom: 16px;
  }
  #workout-edition #workout-form .files-info-box {
    background: var(--r-soft);
    border: 0;
    border-radius: 8px;
    font-size: 12px;
    line-height: 1.6;
  }
  #workout-edition #workout-form .files-help {
    display: block;
    padding: 12px;
  }
  #workout-edition #workout-form .files-help div {
    display: block;
  }
  #workout-edition #workout-form .field-help .info-box {
    border: 0;
    background: transparent;
    padding: 0;
    color: var(--r-muted);
    font-size: 11px;
    line-height: 1.5;
  }
  #workout-edition #workout-form .form-buttons {
    padding: 14px 0 0;
    justify-content: flex-start;
    gap: 12px;
  }
  #workout-edition #workout-form .form-buttons button {
    min-height: 48px;
    padding: 0 22px;
    border-radius: 10px;
    margin: 0;
  }
  #workout-edition #workout-form .form-buttons .confirm {
    background: var(--r-accent);
    color: var(--r-accent-ink);
    border: 0;
    font-weight: 700;
  }
  @media (max-width: 600px) {
    #workout-edition :deep(.card-content) {
      padding: 18px;
    }
    .activity-sharing-fields {
      grid-template-columns: 1fr;
    }
  }
</style>
