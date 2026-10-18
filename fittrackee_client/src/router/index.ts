import { capitalize } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const AdminApplication = () =>
  import('@/components/Administration/AdminApplication.vue')
const AdminEquipmentTypes = () =>
  import('@/components/Administration/AdminEquipmentTypes.vue')
const AdminMenu = () => import('@/components/Administration/AdminMenu.vue')
const AdminQueuedTasksCount = () =>
  import('@/components/Administration/AdminQueuedTasksCount.vue')
const AdminQueuedTasksList = () =>
  import('@/components/Administration/AdminQueuedTasksList.vue')
const AdminReport = () => import('@/components/Administration/AdminReport.vue')
const AdminReports = () =>
  import('@/components/Administration/AdminReports.vue')
const AdminSports = () => import('@/components/Administration/AdminSports.vue')
const AdminUsers = () => import('@/components/Administration/AdminUsers.vue')
const Profile = () => import('@/components/User/ProfileDisplay/index.vue')
const UserAccount = () =>
  import('@/components/User/ProfileDisplay/UserAccount.vue')
const UserInfos = () => import('@/components/User/ProfileDisplay/UserInfos.vue')
const UserNotifications = () =>
  import('@/components/User/ProfileDisplay/UserNotifications.vue')
const UserPreferences = () =>
  import('@/components/User/ProfileDisplay/UserPreferences.vue')
const UsersList = () => import('@/components/User/ProfileDisplay/UsersList.vue')
const UserUIMessages = () =>
  import('@/components/User/ProfileDisplay/UserUIMessages.vue')
const ProfileEdition = () =>
  import('@/components/User/ProfileEdition/index.vue')
const UserAccountEdition = () =>
  import('@/components/User/ProfileEdition/UserAccountEdition.vue')
const UserInfosEdition = () =>
  import('@/components/User/ProfileEdition/UserInfosEdition.vue')
const UserNotificationsEdition = () =>
  import('@/components/User/ProfileEdition/UserNotificationsEdition.vue')
const UserPictureEdition = () =>
  import('@/components/User/ProfileEdition/UserPictureEdition.vue')
const UserPreferencesEdition = () =>
  import('@/components/User/ProfileEdition/UserPreferencesEdition.vue')
const UserPrivacyPolicyValidation = () =>
  import('@/components/User/ProfileEdition/UserPrivacyPolicyValidation.vue')
const UserUIMessageEdition = () =>
  import('@/components/User/ProfileEdition/UserUIMessageEdition.vue')
const UserAccountSuspension = () =>
  import('@/components/User/UserAccountSuspension.vue')
const AddUserApp = () => import('@/components/User/UserApps/AddUserApp.vue')
const AuthorizeUserApp = () =>
  import('@/components/User/UserApps/AuthorizeUserApp.vue')
const UserApps = () => import('@/components/User/UserApps/index.vue')
const UserApp = () => import('@/components/User/UserApps/UserApp.vue')
const UserAppsList = () => import('@/components/User/UserApps/UserAppsList.vue')
const UserArchiveUploads = () =>
  import('@/components/User/UserArchiveUploads/index.vue')
const UserArchiveUploadDetail = () =>
  import('@/components/User/UserArchiveUploads/UserArchiveUploadDetail.vue')
const UserArchiveUploadsList = () =>
  import('@/components/User/UserArchiveUploads/UserArchiveUploadsList.vue')
const EquipmentEdition = () =>
  import('@/components/User/UserEquipments/EquipmentEdition.vue')
const UserEquipments = () =>
  import('@/components/User/UserEquipments/index.vue')
const UserEquipment = () =>
  import('@/components/User/UserEquipments/UserEquipment.vue')
const UserEquipmentsList = () =>
  import('@/components/User/UserEquipments/UserEquipmentsList.vue')
const UserModeration = () =>
  import('@/components/User/UserModeration/index.vue')
const UserSanctionDetail = () =>
  import('@/components/User/UserModeration/UserSanctionDetail.vue')
const UserSanctionsList = () =>
  import('@/components/User/UserModeration/UserSanctionsList.vue')
const UserRelationships = () =>
  import('@/components/User/UserRelationships.vue')
const UserSports = () => import('@/components/User/UserSports/index.vue')
const UserSport = () => import('@/components/User/UserSports/UserSport.vue')
const UserSportEdition = () =>
  import('@/components/User/UserSports/UserSportEdition.vue')
const UserSportPreferences = () =>
  import('@/components/User/UserSports/UserSportPreferences.vue')
import createI18n from '@/i18n'
import store from '@/store'
import {
  AUTH_USER_STORE,
  NOTIFICATIONS_STORE,
  ROOT_STORE,
} from '@/store/constants'
const AboutView = () => import('@/views/AboutView.vue')
const AdminView = () => import('@/views/AdminView.vue')
const Dashboard = () => import('@/views/Dashboard.vue')
const MigrationView = () => import('@/views/MigrationView.vue')
const NotFoundView = () => import('@/views/NotFoundView.vue')
const NotificationsView = () => import('@/views/NotificationsView.vue')
const PrivacyPolicyView = () => import('@/views/PrivacyPolicyView.vue')
const ProgressView = () => import('@/views/ProgressView.vue')
const StatisticsView = () => import('@/views/StatisticsView.vue')
const AccountConfirmationResendView = () =>
  import('@/views/user/AccountConfirmationResendView.vue')
const AccountConfirmationView = () =>
  import('@/views/user/AccountConfirmationView.vue')
const EmailUpdateView = () => import('@/views/user/EmailUpdateView.vue')
const LoginOrRegister = () => import('@/views/user/LoginOrRegister.vue')
const PasswordResetView = () => import('@/views/user/PasswordResetView.vue')
const ProfileView = () => import('@/views/user/ProfileView.vue')
const UserView = () => import('@/views/user/UserView.vue')
const UsersView = () => import('@/views/UsersView.vue')
const AddWorkout = () => import('@/views/workouts/AddWorkout.vue')
const CommentView = () => import('@/views/workouts/CommentView.vue')
const EditWorkout = () => import('@/views/workouts/EditWorkout.vue')
const Likes = () => import('@/views/workouts/Likes.vue')
const Workout = () => import('@/views/workouts/Workout.vue')
const WorkoutsGlobalMapView = () =>
  import('@/views/workouts/WorkoutsGlobalMapView.vue')
const WorkoutsView = () => import('@/views/workouts/WorkoutsView.vue')

const { t } = createI18n.global

const getTabFromPath = (path: string): string => {
  const regex = /(\/profile)(\/edit)*(\/*)/
  const tab = path.replace(regex, '').toUpperCase()
  return tab === '' ? 'PROFILE' : tab.split('/')[0].toUpperCase()
}

const routes: RouteRecordRaw[] = [
  {
    path: '/progress',
    name: 'Progress',
    component: ProgressView,
    meta: { title: 'Training progress', allowedToSuspendedUser: false },
  },
  {
    path: '/migration',
    name: 'Migration',
    component: MigrationView,
    meta: { title: 'Workout history', allowedToSuspendedUser: false },
  },
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard,
    meta: {
      title: 'dashboard.DASHBOARD',
      allowedToSuspendedUser: false,
    },
  },
  {
    path: '/login',
    name: 'Login',
    component: LoginOrRegister,
    props: { action: 'login' },
    meta: {
      title: 'user.LOGIN',
      withoutAuth: true,
    },
  },
  {
    path: '/register',
    name: 'Register',
    component: LoginOrRegister,
    props: { action: 'register' },
    meta: {
      title: 'user.REGISTER',
      withoutAuth: true,
    },
  },
  {
    path: '/account-confirmation',
    name: 'AccountConfirmation',
    component: AccountConfirmationView,
    meta: {
      title: 'user.ACCOUNT_CONFIRMATION',
      withoutAuth: true,
    },
  },
  {
    path: '/account-confirmation/resend',
    name: 'AccountConfirmationResend',
    component: AccountConfirmationResendView,
    props: { action: 'account-confirmation-resend' },
    meta: {
      title: 'buttons.ACCOUNT-CONFIRMATION-RESEND',
      withoutAuth: true,
    },
  },
  {
    path: '/account-confirmation/email-sent',
    name: 'AccountConfirmationEmailSend',
    component: AccountConfirmationResendView,
    props: { action: 'email-sent' },
    meta: {
      title: 'buttons.ACCOUNT-CONFIRMATION-RESEND',
      withoutAuth: true,
    },
  },
  {
    path: '/password-reset/sent',
    name: 'PasswordEmailSent',
    component: PasswordResetView,
    props: { action: 'request-sent' },
    meta: {
      title: 'user.PASSWORD_RESET',
      withoutAuth: true,
    },
  },
  {
    path: '/password-reset/request',
    name: 'PasswordResetRequest',
    component: PasswordResetView,
    props: { action: 'reset-request' },
    meta: {
      title: 'user.PASSWORD_RESET',
      withoutAuth: true,
    },
  },
  {
    path: '/password-reset/password-updated',
    name: 'PasswordUpdated',
    component: PasswordResetView,
    props: { action: 'password-updated' },
    meta: {
      title: 'user.PASSWORD_RESET',
      withoutAuth: true,
    },
  },
  {
    path: '/password-reset',
    name: 'PasswordReset',
    component: PasswordResetView,
    props: { action: 'reset' },
    meta: {
      title: 'user.PASSWORD_RESET',
      withoutAuth: true,
    },
  },
  {
    path: '/email-update',
    name: 'EmailUpdate',
    component: EmailUpdateView,
    meta: {
      title: 'user.EMAIL_UPDATE',
      withoutChecks: true,
    },
  },
  {
    path: '/profile',
    name: 'Profile',
    component: ProfileView,
    children: [
      {
        path: '',
        name: 'UserProfile',
        component: Profile,
        props: (route) => ({
          tab: getTabFromPath(route.path),
        }),
        children: [
          {
            path: '',
            name: 'UserInfos',
            component: UserInfos,
            meta: {
              title: 'user.PROFILE.TABS.PROFILE',
            },
          },
          {
            path: 'account',
            name: 'UserAccount',
            component: UserAccount,
            meta: {
              title: 'user.PROFILE.TABS.ACCOUNT',
            },
          },
          {
            path: 'preferences',
            name: 'UserPreferences',
            component: UserPreferences,
            meta: {
              title: 'user.PROFILE.TABS.PREFERENCES',
            },
          },
          {
            path: 'notifications',
            name: 'UserNotifications',
            component: UserNotifications,
            meta: {
              title: 'user.PROFILE.TABS.NOTIFICATIONS',
            },
          },
          {
            path: 'messages',
            name: 'UserUIMessages',
            component: UserUIMessages,
            meta: {
              title: 'user.PROFILE.TABS.MESSAGES',
            },
          },
          {
            path: 'sports',
            name: 'UserSports',
            component: UserSports,
            props: { isEdition: false },
            meta: {
              title: 'user.PROFILE.TABS.SPORTS',
            },
            children: [
              {
                path: '',
                name: 'UserSportPreferences',
                component: UserSportPreferences,
                meta: {
                  title: 'user.PROFILE.TABS.SPORTS',
                },
              },
              {
                path: ':id',
                name: 'UserSport',
                component: UserSport,
                meta: {
                  title: 'user.PROFILE.TABS.SPORTS',
                },
              },
            ],
          },
          {
            path: 'apps',
            name: 'UserApps',
            component: UserApps,
            children: [
              {
                path: '',
                name: 'UserAppsList',
                component: UserAppsList,
                meta: {
                  title: 'user.PROFILE.TABS.APPS',
                },
              },
              {
                path: ':id',
                name: 'UserApp',
                component: UserApp,
                meta: {
                  title: 'user.PROFILE.TABS.APPS',
                },
              },
              {
                path: ':id/created',
                name: 'CreatedUserApp',
                component: UserApp,
                props: { afterCreation: true },
                meta: {
                  title: 'user.PROFILE.TABS.APPS',
                },
              },
              {
                path: 'new',
                name: 'AddUserApp',
                component: AddUserApp,
                meta: {
                  title: 'user.PROFILE.TABS.APPS',
                },
              },
              {
                path: 'authorize',
                name: 'AuthorizeUserApp',
                component: AuthorizeUserApp,
                meta: {
                  title: 'user.PROFILE.TABS.APPS',
                },
              },
            ],
          },
          {
            path: 'equipments',
            name: 'UserEquipments',
            component: UserEquipments,
            props: { isEdition: false },
            children: [
              {
                path: '',
                name: 'UserEquipmentsList',
                component: UserEquipmentsList,
                meta: {
                  title: 'user.PROFILE.TABS.EQUIPMENTS',
                },
              },
              {
                path: 'new',
                name: 'AddEquipment',
                component: EquipmentEdition,
                meta: {
                  title: 'user.PROFILE.TABS.EQUIPMENTS',
                },
              },
              {
                path: ':id',
                name: 'Equipment',
                component: UserEquipment,
                meta: {
                  title: 'user.PROFILE.TABS.EQUIPMENTS',
                },
              },
            ],
          },
          {
            path: 'follow-requests',
            name: 'FollowRequests',
            component: UsersList,
            props: { itemType: 'follow-requests' },
            meta: {
              title: 'user.PROFILE.TABS.FOLLOW-REQUESTS',
            },
          },
          {
            path: 'blocked-users',
            name: 'BlockedUsers',
            component: UsersList,
            props: { itemType: 'blocked-users' },
            meta: {
              title: 'user.PROFILE.TABS.BLOCKED-USERS',
            },
          },
          {
            path: 'followers',
            name: 'AuthUserFollowers',
            component: UserRelationships,
            props: { relationship: 'followers' },
            meta: {
              title: 'user.RELATIONSHIPS.FOLLOWER',
              count: 0,
            },
          },
          {
            path: 'following',
            name: 'AuthUserFollowing',
            component: UserRelationships,
            props: { relationship: 'following' },
            meta: {
              title: 'user.RELATIONSHIPS.FOLLOWING',
              count: 0,
            },
          },
          {
            path: 'suspension',
            name: 'AuthUserAccountSuspension',
            component: UserAccountSuspension,
          },
          {
            path: 'moderation',
            name: 'Moderation',
            component: UserModeration,
            meta: {
              title: 'user.PROFILE.TABS.MODERATION',
            },
            children: [
              {
                path: '',
                name: 'UserSanctionList',
                component: UserSanctionsList,
              },
              {
                path: 'sanctions/:action_id',
                name: 'UserSanctionDetail',
                component: UserSanctionDetail,
              },
            ],
          },
          {
            path: 'archive-uploads',
            name: 'UserArchiveUploads',
            component: UserArchiveUploads,
            children: [
              {
                path: '',
                name: 'UserArchiveUploadsList',
                component: UserArchiveUploadsList,
                meta: {
                  title: 'user.PROFILE.TABS.ARCHIVE-UPLOADS',
                },
              },
              {
                path: ':task_id',
                name: 'UserArchiveUploadDetail',
                component: UserArchiveUploadDetail,
                meta: {
                  title: 'user.PROFILE.TABS.ARCHIVE-UPLOADS',
                },
              },
            ],
          },
        ],
      },
      {
        path: 'edit',
        name: 'UserProfileEdition',
        component: ProfileEdition,
        props: (route) => ({
          tab: getTabFromPath(route.path),
        }),
        children: [
          {
            path: '',
            name: 'UserInfosEdition',
            component: UserInfosEdition,
            meta: {
              title: 'user.PROFILE.EDIT',
            },
          },
          {
            path: 'account',
            name: 'UserAccountEdition',
            component: UserAccountEdition,
            meta: {
              title: 'user.PROFILE.ACCOUNT_EDITION',
            },
          },
          {
            path: 'picture',
            name: 'UserPictureEdition',
            component: UserPictureEdition,
            meta: {
              title: 'user.PROFILE.PICTURE_EDITION',
            },
          },
          {
            path: 'preferences',
            name: 'UserPreferencesEdition',
            component: UserPreferencesEdition,
            meta: {
              title: 'user.PROFILE.EDIT_PREFERENCES',
            },
          },
          {
            path: 'notifications',
            name: 'UserNotificationsEdition',
            component: UserNotificationsEdition,
            meta: {
              title: 'user.PROFILE.EDIT_NOTIFICATIONS',
            },
          },
          {
            path: 'messages',
            name: 'UserUIMessageEdition',
            component: UserUIMessageEdition,
            meta: {
              title: 'user.PROFILE.EDIT_MESSAGES_PREFERENCES',
            },
          },
          {
            path: 'sports',
            name: 'UserSportsEdition',
            component: UserSports,
            props: { isEdition: true },
            meta: {
              title: 'user.PROFILE.EDIT_SPORTS_PREFERENCES',
            },
            children: [
              {
                path: '',
                name: 'UserSportPreferencesEdition',
                component: UserSportPreferences,
                meta: {
                  title: 'user.PROFILE.TABS.SPORTS',
                },
              },
              {
                path: ':id',
                name: 'UserSportEdition',
                component: UserSportEdition,
                meta: {
                  title: 'user.PROFILE.TABS.SPORTS',
                },
              },
            ],
          },
          {
            path: 'equipments',
            name: 'UserEquipmentsEdition',
            component: UserEquipments,
            props: { isEdition: true },
            children: [
              {
                path: '',
                name: 'UserEquipmentsListEdition',
                component: UserEquipmentsList,
                meta: {
                  title: 'user.PROFILE.TABS.EQUIPMENTS',
                },
              },
              {
                path: ':id',
                name: 'EquipmentEdition',
                component: EquipmentEdition,
                meta: {
                  title: 'user.PROFILE.TABS.EQUIPMENTS',
                },
              },
            ],
          },
          {
            path: 'privacy-policy',
            name: 'UserPrivacyPolicy',
            component: UserPrivacyPolicyValidation,
            meta: {
              title: 'user.PROFILE.PRIVACY-POLICY_EDITION',
            },
          },
        ],
      },
    ],
  },
  {
    path: '/notifications',
    name: 'Notifications',
    component: NotificationsView,
    meta: {
      allowedToSuspendedUser: false,
    },
  },
  {
    path: '/statistics',
    name: 'Statistics',
    component: StatisticsView,
    meta: {
      title: 'statistics.STATISTICS',
      allowedToSuspendedUser: false,
    },
  },
  {
    path: '/users',
    name: 'Users',
    component: UsersView,
    meta: {
      allowedToSuspendedUser: false,
    },
  },
  {
    path: '/users/:username',
    name: 'User',
    props: { fromAdmin: false },
    component: UserView,
    meta: {
      title: 'user.USER',
      withoutChecks: true,
      allowedToSuspendedUser: false,
    },
    children: [
      {
        path: 'followers',
        name: 'UserFollowers',
        component: UserRelationships,
        props: { relationship: 'followers' },
        meta: {
          withoutAuth: false,
          withoutChecks: false,
        },
      },
      {
        path: 'following',
        name: 'UserFollowing',
        component: UserRelationships,
        props: { relationship: 'following' },
        meta: {
          withoutAuth: false,
          withoutChecks: false,
        },
      },
    ],
  },
  {
    path: '/workouts',
    name: 'Workouts',
    component: WorkoutsView,
    meta: {
      title: 'workouts.WORKOUT',
      count: 0,
      allowedToSuspendedUser: false,
    },
  },
  {
    path: '/workouts/map',
    name: 'WorkoutsMap',
    component: WorkoutsGlobalMapView,
    meta: {
      title: 'workouts.WORKOUTS_MAP',
      count: 0,
      allowedToSuspendedUser: false,
    },
  },
  {
    path: '/workouts/:workoutId',
    name: 'Workout',
    component: Workout,
    props: { displaySegment: false },
    meta: {
      title: 'workouts.WORKOUT',
      withoutChecks: true,
      allowedToSuspendedUser: false,
    },
  },
  {
    path: '/workouts/:workoutId/likes',
    name: 'WorkoutLikes',
    component: Likes,
    props: { objectType: 'workout' },
    meta: {
      title: 'workouts.LIKES',
      withoutChecks: true,
      allowedToSuspendedUser: false,
    },
  },
  {
    path: '/workouts/:workoutId/edit',
    name: 'EditWorkout',
    component: EditWorkout,
    meta: {
      title: 'workouts.EDIT_WORKOUT',
      allowedToSuspendedUser: false,
    },
  },
  {
    path: '/workouts/:workoutId/segment/:segmentId',
    name: 'WorkoutSegment',
    component: Workout,
    props: { displaySegment: true },
    meta: {
      title: 'workouts.SEGMENT',
      count: 0,
      withoutChecks: true,
      allowedToSuspendedUser: false,
    },
  },
  {
    path: '/workouts/:workoutId/comments/:commentId',
    name: 'WorkoutComment',
    component: Workout,
    props: { displaySegment: false },
    meta: {
      allowedToSuspendedUser: false,
      withoutChecks: true,
    },
  },
  {
    path: '/workouts/:workoutId/comments/:commentId/likes',
    name: 'WorkoutCommentLikes',
    component: Likes,
    props: { objectType: 'comment' },
    meta: {
      title: 'workouts.LIKES',
      withoutChecks: true,
      allowedToSuspendedUser: false,
    },
  },
  {
    path: '/comments/:commentId',
    name: 'Comment',
    component: CommentView,
    meta: {
      allowedToSuspendedUser: false,
      withoutChecks: true,
    },
  },
  {
    path: '/comments/:commentId/likes',
    name: 'CommentLikes',
    component: Likes,
    props: { objectType: 'comment' },
    meta: {
      title: 'workouts.LIKES',
      withoutChecks: true,
      allowedToSuspendedUser: false,
    },
  },
  {
    path: '/workouts/add',
    name: 'AddWorkout',
    component: AddWorkout,
    meta: {
      title: 'workouts.ADD_WORKOUT',
      allowedToSuspendedUser: false,
    },
  },
  {
    path: '/admin',
    name: 'Administration',
    component: AdminView,
    meta: {
      allowedToSuspendedUser: false,
      minimumRole: 'moderator',
    },
    children: [
      {
        path: '',
        name: 'AdministrationMenu',
        component: AdminMenu,
        meta: {
          title: 'admin.ADMINISTRATION',
        },
      },
      {
        path: 'application',
        name: 'ApplicationAdministration',
        component: AdminApplication,
        meta: {
          title: 'admin.APP_CONFIG.TITLE',
          minimumRole: 'admin',
        },
      },
      {
        path: 'application/edit',
        name: 'ApplicationAdministrationEdition',
        component: AdminApplication,
        props: { edition: true },
        meta: {
          title: 'admin.APPLICATION',
          minimumRole: 'admin',
        },
      },
      {
        path: 'equipment-types',
        name: 'EquipmentTypeAdministration',
        component: AdminEquipmentTypes,
        meta: {
          title: 'admin.EQUIPMENT_TYPES.TITLE',
          minimumRole: 'admin',
        },
      },
      {
        path: 'sports',
        name: 'SportsAdministration',
        component: AdminSports,
        meta: {
          title: 'admin.SPORTS.TITLE',
          minimumRole: 'admin',
        },
      },
      {
        path: 'reports',
        name: 'ReportsAdministration',
        component: AdminReports,
        meta: {
          title: 'admin.APP_MODERATION.TITLE',
        },
      },
      {
        path: 'reports/:reportId',
        name: 'ReportAdministration',
        component: AdminReport,
        meta: {
          title: 'admin.APP_MODERATION.REPORT',
        },
      },
      {
        path: 'users/:username',
        name: 'UserFromAdmin',
        component: UserView,
        props: { fromAdmin: true },
        meta: {
          title: 'admin.USER',
          count: 1,
        },
      },
      {
        path: 'users',
        name: 'UsersAdministration',
        component: AdminUsers,
        meta: {
          title: 'admin.USERS.TITLE',
          minimumRole: 'admin',
        },
      },
      {
        path: 'queued-tasks',
        name: 'QueuedTasksCountAdministration',
        component: AdminQueuedTasksCount,
        meta: {
          title: 'admin.USERS_QUEUED_TASKS.LABEL',
          minimumRole: 'admin',
        },
      },
      {
        path: 'queued-tasks/:taskType',
        name: 'QueuedTaskListAdministration',
        component: AdminQueuedTasksList,
        meta: {
          title: 'admin.USERS_QUEUED_TASKS.LABEL',
          minimumRole: 'admin',
        },
      },
    ],
  },
  {
    path: '/about',
    name: 'About',
    component: AboutView,
    meta: {
      title: 'common.ABOUT',
      withoutChecks: true,
    },
  },
  {
    path: '/privacy-policy',
    name: 'PrivacyPolicy',
    component: PrivacyPolicyView,
    meta: {
      title: 'privacy_policy.TITLE',
      withoutChecks: true,
    },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: NotFoundView,
    meta: {
      title: 'error.NOT_FOUND.PAGE',
    },
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) return savedPosition
    if (to.path !== from.path) return { left: 0, top: 0 }
    // Workout detail waits for its asynchronous content before following hashes.
    if (to.hash && document.getElementById(to.hash.slice(1))) {
      return { el: to.hash, top: 16 }
    }
    return false
  },
})

router.beforeEach((to, from, next) => {
  if ('title' in to.meta) {
    const title = typeof to.meta.title === 'string' ? to.meta.title : ''
    const translatedTitle = title
      ? typeof to.meta.count === 'number'
        ? t(title, +to.meta.count)
        : t(title)
      : ''
    window.document.title = `Rint${
      title ? ` - ${capitalize(translatedTitle)}` : ''
    }`
  }
  store.commit(ROOT_STORE.MUTATIONS.EMPTY_ERROR_MESSAGES)
  store
    .dispatch(AUTH_USER_STORE.ACTIONS.CHECK_AUTH_USER)
    .then(() => {
      if (to.meta.withoutChecks) {
        return next()
      }

      if (
        store.getters[AUTH_USER_STORE.GETTERS.IS_PROFILE_LOADED] &&
        store.getters[AUTH_USER_STORE.GETTERS.IS_SUSPENDED] &&
        !to.path.startsWith('/profile') &&
        !to.meta.allowedToSuspendedUser
      ) {
        return next('/profile')
      }

      if (
        store.getters[AUTH_USER_STORE.GETTERS.IS_AUTHENTICATED] &&
        store.getters[AUTH_USER_STORE.GETTERS.IS_PROFILE_LOADED] &&
        !store.getters[AUTH_USER_STORE.GETTERS.IS_SUSPENDED]
      ) {
        store.dispatch(NOTIFICATIONS_STORE.ACTIONS.GET_UNREAD_STATUS)
      }

      if (
        store.getters[AUTH_USER_STORE.GETTERS.IS_AUTHENTICATED] &&
        to.meta.withoutAuth
      ) {
        return next('/')
      }

      if (
        !store.getters[AUTH_USER_STORE.GETTERS.IS_AUTHENTICATED] &&
        !to.meta.withoutAuth
      ) {
        const path =
          to.path === '/'
            ? { path: '/login' }
            : { path: '/login', query: { from: to.fullPath } }
        next(path)
      } else {
        next()
      }
    })
    .catch((error) => {
      console.error(error)
      next()
    })
})

export default router
