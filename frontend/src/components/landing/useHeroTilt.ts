import { type MouseEvent, useCallback, useRef } from "react";
import { useMotionValue, useReducedMotion, useSpring } from "motion/react";

const MAX_TILT = 6;

export function useHeroTilt() {
  const ref = useRef<HTMLDivElement>(null);
  const reduce = useReducedMotion();
  const rotateX = useMotionValue(0);
  const rotateY = useMotionValue(0);
  const springX = useSpring(rotateX, { stiffness: 180, damping: 22 });
  const springY = useSpring(rotateY, { stiffness: 180, damping: 22 });

  const onMove = useCallback(
    (e: MouseEvent<HTMLDivElement>) => {
      if (reduce || !ref.current) return;
      const rect = ref.current.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width - 0.5;
      const y = (e.clientY - rect.top) / rect.height - 0.5;
      rotateY.set(x * MAX_TILT * 2);
      rotateX.set(-y * MAX_TILT * 2);
    },
    [reduce, rotateX, rotateY],
  );

  const onLeave = useCallback(() => {
    rotateX.set(0);
    rotateY.set(0);
  }, [rotateX, rotateY]);

  return {
    ref,
    onMove,
    onLeave,
    style: reduce
      ? undefined
      : {
          rotateX: springX,
          rotateY: springY,
          transformPerspective: 1200,
        },
  };
}
