import clsx from 'clsx';

function ContentContainer({ className, children }) {
  return <div className={clsx('mx-auto flex max-w-6xl flex-col gap-5 p-4 sm:p-6', className)}>{children}</div>;
}

export default ContentContainer;
