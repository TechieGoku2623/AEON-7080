"use client";

import { OrbitControls } from "@react-three/drei";
import { Canvas, useFrame } from "@react-three/fiber";
import { useRef } from "react";
import type { Mesh } from "three";
import { glucoseColor } from "@/lib/utils";

function Heart({ rate, color }: { rate: number; color: string }) {
  const ref = useRef<Mesh>(null);
  useFrame(({ clock }) => {
    const pulse = 1 + 0.08 * Math.sin(clock.elapsedTime * Math.max(rate, 40) / 18);
    ref.current?.scale.setScalar(pulse);
  });
  return (
    <mesh ref={ref} position={[0.12, 0.35, 0.12]}>
      <sphereGeometry args={[0.16, 28, 28]} />
      <meshStandardMaterial color={color} roughness={0.35} />
    </mesh>
  );
}

function Schematic({ glucose, heartRate, concentration }: { glucose: number; heartRate: number; concentration: number }) {
  const glucoseTint = glucoseColor(glucose);
  const drugTint = `hsl(${200 - Math.min(concentration, 20) * 6} 70% 62%)`;
  return (
    <>
      <ambientLight intensity={0.7} />
      <directionalLight position={[3, 4, 2]} intensity={1.4} />
      <mesh position={[0, 0.1, 0]}>
        <capsuleGeometry args={[0.42, 1.15, 8, 24]} />
        <meshStandardMaterial color="#163140" roughness={0.7} transparent opacity={0.55} />
      </mesh>
      <mesh position={[0, 1.15, 0]}>
        <sphereGeometry args={[0.22, 28, 28]} />
        <meshStandardMaterial color="#8fd0c4" />
      </mesh>
      <Heart rate={heartRate} color="#d36b6b" />
      <mesh position={[-0.22, 0.42, 0.05]}>
        <sphereGeometry args={[0.16, 24, 24]} />
        <meshStandardMaterial color="#7ea2b5" />
      </mesh>
      <mesh position={[0.28, 0.48, 0]}>
        <sphereGeometry args={[0.15, 24, 24]} />
        <meshStandardMaterial color="#7ea2b5" />
      </mesh>
      <mesh position={[-0.16, 0.05, 0.16]}>
        <sphereGeometry args={[0.18, 24, 24]} />
        <meshStandardMaterial color={drugTint} />
      </mesh>
      <mesh position={[0.22, -0.25, 0.08]}>
        <sphereGeometry args={[0.1, 20, 20]} />
        <meshStandardMaterial color="#c9896a" />
      </mesh>
      <mesh position={[-0.22, -0.25, 0.08]}>
        <sphereGeometry args={[0.1, 20, 20]} />
        <meshStandardMaterial color="#c9896a" />
      </mesh>
      <mesh position={[0.02, 0.02, 0.2]}>
        <sphereGeometry args={[0.08, 20, 20]} />
        <meshStandardMaterial color={glucoseTint} emissive={glucoseTint} emissiveIntensity={0.25} />
      </mesh>
      <mesh position={[0, -0.85, 0]}>
        <boxGeometry args={[0.7, 0.08, 0.25]} />
        <meshStandardMaterial color="#355868" />
      </mesh>
      <OrbitControls enablePan={false} minDistance={2.2} maxDistance={6} />
    </>
  );
}

export function DigitalHuman({
  glucose = 100,
  heartRate = 72,
  concentration = 0,
}: {
  glucose?: number;
  heartRate?: number;
  concentration?: number;
}) {
  return (
    <div className="relative h-[340px] overflow-hidden rounded-xl border border-line bg-[#08141c]">
      <Canvas camera={{ position: [0, 0.2, 3.4], fov: 42 }}>
        <Schematic glucose={glucose} heartRate={heartRate} concentration={concentration} />
      </Canvas>
      <div className="pointer-events-none absolute inset-x-0 bottom-0 bg-gradient-to-t from-ink/80 p-3 text-xs text-mute">
        Simplified schematic. Pancreas color tracks simulated glucose. Liver color tracks simulated concentration. Heart scale tracks rate. Not anatomy.
      </div>
    </div>
  );
}
