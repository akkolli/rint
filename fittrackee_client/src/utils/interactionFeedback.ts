import { ref } from 'vue'

const key = 'rint-interaction-sounds'
function readPreference() {
  try {
    return localStorage.getItem(key) === 'on'
  } catch {
    return false
  }
}
export const interactionSounds = ref(readPreference())
let context: AudioContext | undefined

export function prepareFeedback() {
  if (!interactionSounds.value) return
  try {
    context ??= new AudioContext()
    void context.resume().catch(() => {})
  } catch {
    // Feedback is optional, including in browsers without Web Audio.
  }
}
export function playAppreciation() {
  if (!interactionSounds.value || !context || context.state !== 'running')
    return
  try {
    const now = context.currentTime
    for (const [frequency, delay] of [
      [660, 0],
      [880, 0.035],
    ]) {
      const tone = context.createOscillator()
      const gain = context.createGain()
      tone.frequency.value = frequency
      gain.gain.setValueAtTime(0, now + delay)
      gain.gain.linearRampToValueAtTime(0.035, now + delay + 0.008)
      gain.gain.exponentialRampToValueAtTime(0.0001, now + delay + 0.13)
      tone.connect(gain)
      gain.connect(context.destination)
      tone.start(now + delay)
      tone.stop(now + delay + 0.14)
      tone.onended = () => {
        tone.disconnect()
        gain.disconnect()
      }
    }
  } catch {
    // Never interrupt an action because optional audio is unavailable.
  }
}
export function toggleInteractionSounds() {
  interactionSounds.value = !interactionSounds.value
  try {
    localStorage.setItem(key, interactionSounds.value ? 'on' : 'off')
  } catch {
    /* Session preference still works. */
  }
  prepareFeedback()
}
