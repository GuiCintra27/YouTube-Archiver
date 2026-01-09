import type { ReactNode } from "react";

type VideoGridHeaderProps = {
  icon: ReactNode;
  title: string;
  subtitle?: string;
  rightSlot?: ReactNode;
};

export default function VideoGridHeader({
  icon,
  title,
  subtitle,
  rightSlot,
}: VideoGridHeaderProps) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div className="flex items-center gap-3">
        <div className="icon-glow p-2">{icon}</div>
        <div>
          <h2 className="text-xl font-bold text-white">{title}</h2>
          {subtitle ? (
            <p className="text-sm text-muted-foreground">{subtitle}</p>
          ) : null}
        </div>
      </div>
      {rightSlot}
    </div>
  );
}
