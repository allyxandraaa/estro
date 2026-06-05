import client from './client.js'

export async function completeOnboarding({ cycle_length, period_length }) {
  return client.post('/users/onboarding', { cycle_length, period_length })
}
