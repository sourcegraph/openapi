export interface SSE {
  event: string;
  data: unknown;
}
export function parseSSE(reponseBody: string): SSE[] {
  const lines = reponseBody.split("\n");
  const events: SSE[] = [];
  let currentEvent: Partial<SSE> = {};

  for (const line of lines) {
    if (line.startsWith("event:")) {
      currentEvent.event = line.slice(6).trim();
    } else if (line.startsWith("data:")) {
      currentEvent.data = JSON.parse(line.slice("data:".length).trim());
    } else if (line === "") {
      if (currentEvent.event && currentEvent.data) {
        events.push(currentEvent as SSE);
        currentEvent = {};
      }
    }
  }

  // Push the last event if it's complete
  if (currentEvent.event && currentEvent.data) {
    events.push(currentEvent as SSE);
  }

  return events;
}
