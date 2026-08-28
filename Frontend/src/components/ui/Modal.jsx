import { useEffect, useRef } from 'react';
import { X } from 'lucide-react';
import IconButton from './IconButton';

/** Built on the native <dialog> element for built-in focus trapping and Esc
 * handling instead of pulling in a dialog library. */
function Modal({ open, onClose, title, children, className = '' }) {
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
      className={`m-auto w-full max-w-lg rounded-lg border border-slate-200 bg-white p-0 shadow-xl backdrop:bg-slate-900/40 ${className}`}
    >
      {open && (
        <div className="p-5">
          <div className="mb-4 flex items-center justify-between gap-3">
            <h2 className="text-base font-semibold text-slate-900">{title}</h2>
            <IconButton label="Close" onClick={() => onClose?.()}>
              <X className="size-4" aria-hidden="true" />
            </IconButton>
          </div>
          {children}
        </div>
      )}
    </dialog>
  );
}

export default Modal;
