import clsx from 'clsx';

function Skeleton({ className }) {
  return <div className={clsx('animate-pulse rounded-md bg-slate-200', className)} aria-hidden="true" />;
}

function SkeletonList({ rows = 3, className }) {
  return (
    <div className={clsx('flex flex-col gap-2', className)} aria-hidden="true">
      {Array.from({ length: rows }).map((_, index) => (
        <Skeleton key={index} className="h-16 w-full" />
      ))}
    </div>
  );
}

Skeleton.List = SkeletonList;

export default Skeleton;
