import type { TraceEvent } from "../api/types";

interface TraceTimelineProps {
  trace: TraceEvent[];
}

export function TraceTimeline({ trace }: TraceTimelineProps) {
  return (
    <div className="timeline">
      {trace.length === 0 ? (
        <p className="empty">暂无持久化 Trace 事件。</p>
      ) : (
        trace.map((event, index) => (
          <article className="timeline-item" key={`${event.node ?? "node"}-${index}`}>
            <strong>{event.node ?? "unknown_node"}</strong>
            <span>{event.timestamp ?? "无时间戳"}</span>
            <p>{event.output_summary ?? "暂无摘要"}</p>
          </article>
        ))
      )}
    </div>
  );
}
