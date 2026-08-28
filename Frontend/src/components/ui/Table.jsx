import clsx from 'clsx';

/** Dense tabular data with a horizontal-scroll wrapper for small screens
 * (per the design brief: wide tables scroll in their own container rather
 * than reflowing into cards). */
function Table({ className, children, ...props }) {
  return (
    <div className="w-full overflow-x-auto rounded-lg border border-slate-200">
      <table className={clsx('w-full min-w-max border-collapse text-sm', className)} {...props}>
        {children}
      </table>
    </div>
  );
}

function Thead({ children }) {
  return <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">{children}</thead>;
}

function Th({ className, children, ...props }) {
  return (
    <th className={clsx('border-b border-slate-200 px-3 py-2.5', className)} {...props}>
      {children}
    </th>
  );
}

function Tbody({ className, children }) {
  return <tbody className={clsx('divide-y divide-slate-100', className)}>{children}</tbody>;
}

function Tr({ className, children, ...props }) {
  return (
    <tr className={clsx('hover:bg-slate-50', className)} {...props}>
      {children}
    </tr>
  );
}

function Td({ className, children, ...props }) {
  return (
    <td className={clsx('px-3 py-2.5 align-middle text-slate-700', className)} {...props}>
      {children}
    </td>
  );
}

Table.Head = Thead;
Table.Th = Th;
Table.Body = Tbody;
Table.Tr = Tr;
Table.Td = Td;

export default Table;
