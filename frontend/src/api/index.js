// Barrel for the api/ module. Add per-page modules here as the app grows:
//   export * as auth    from './auth.js'
//   export * as profile from './profile.js'
//   export * as orders  from './orders.js'

export * as auth from './auth.js'
export { api, ApiError } from './client.js'
