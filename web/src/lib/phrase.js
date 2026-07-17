const KEY = 'video-agent-access-phrase'

export function loadPhrase() {
  try {
    return sessionStorage.getItem(KEY) || ''
  } catch {
    return ''
  }
}

export function savePhrase(phrase) {
  try {
    if (phrase) sessionStorage.setItem(KEY, phrase)
    else sessionStorage.removeItem(KEY)
  } catch {
    /* ignore */
  }
}
