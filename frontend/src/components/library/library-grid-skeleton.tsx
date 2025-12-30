export default function LibraryGridSkeleton() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {Array.from({ length: 12 }).map((_, index) => (
        <div
          key={index}
          className="glass-card rounded-xl overflow-hidden animate-pulse"
        >
          <div className="aspect-video bg-white/5" />
          <div className="p-4 space-y-2">
            <div className="h-4 w-3/4 rounded-full bg-white/10" />
            <div className="h-3 w-1/2 rounded-full bg-white/5" />
          </div>
        </div>
      ))}
    </div>
  );
}
