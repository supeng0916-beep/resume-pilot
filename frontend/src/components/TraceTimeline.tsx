import type { TraceEvent } from "../api/types";

interface TraceTimelineProps {
  trace: TraceEvent[];
}

export function TraceTimeline({ trace }: TraceTimelineProps) {
  return (
    <div className="timeline">
      {trace.length === 0 ? (
        <p className="empty">No trace events persisted.</p>
      ) : (
        trace.map((event, index) => (
          <article className="timeline-item" key={`${event.node ?? "node"}-${index}`}>
            <strong>{event.node ?? "unknown_node"}</strong>
            <span>{event.timestamp ?? "no timestamp"}</span>
            <p>{event.output_summary ?? "No summary"}</p>
          </article>
        ))
      )}
    </div>
  );
}
