import clsx from 'clsx';

function Card({ as: Tag = 'div', padded = true, className, children, ...props }) {
  return (
    <Tag
      className={clsx(
        'rounded-lg border border-slate-200 bg-white shadow-sm',
        padded && 'p-4 sm:p-5',
        className,
      )}
      {...props}
    >
      {children}
    </Tag>
  );
}

function CardHeader({ className, children, ...props }) {
  return (
    <div className={clsx('mb-3 flex items-center justify-between gap-3', className)} {...props}>
      {children}
    </div>
  );
}

function CardTitle({ className, children, ...props }) {
  return (
    <h2 className={clsx('text-base font-semibold text-slate-900', className)} {...props}>
      {children}
    </h2>
  );
}

Card.Header = CardHeader;
Card.Title = CardTitle;

export default Card;
