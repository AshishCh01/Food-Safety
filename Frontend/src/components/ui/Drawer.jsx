import { useEffect, useRef } from 'react';
import { X } from 'lucide-react';
import clsx from 'clsx';
import IconButton from './IconButton';

/** Full-height side panel built on native <dialog>, used for the mobile nav
 * drawer and detail side-panels. `side` is 'left' (nav) or 'right' (detail). */
function Drawer({ open, onClose, title, side = 'right', children, widthClassName = 'max-w-sm', bare = false }) {
  const dialogRef = useRef(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      dialog.showModal();
    } else if (!open && dialog.open) {
      dialog.close();
    }
  }, [open]);

  return (
    <dialog
      ref={dialogRef}
      onCancel={(event) => {
        event.preventDefault();
        onClose?.();
      }}
      onClose={() => onClose?.()}
      onClick={(event) => {
        if (event.target === dialogRef.current) onClose?.();
      }}
      className={clsx(
        'my-0 h-dvh w-full border-0 p-0 shadow-xl backdrop:bg-slate-900/40',
        widthClassName,
        side === 'left' ? 'left-0 ml-0 mr-auto' : 'right-0 mr-0 ml-auto',
      )}
    >
      {open && bare && <div className="h-full overflow-y-auto">{children}</div>}
      {open && !bare && (
        <div className="flex h-full flex-col overflow-y-auto p-4">
          <div className="mb-4 flex items-center justify-between gap-3">
            {title && <h2 className="text-base font-semibold text-slate-900">{title}</h2>}
            <IconButton label="Close" onClick={() => onClose?.()} className="ml-auto">
              <X className="size-4" aria-hidden="true" />
            </IconButton>
          </div>
          {children}
        </div>
      )}
    </dialog>
  );
}

export default Drawer;
