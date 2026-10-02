export default function Logo({ size = 36 }) {
  return (
    <img
      src="/simdaa-logo.png"
      alt="Simdaa Technologies"
      width={size}
      height={size}
      style={{ objectFit: "contain", display: "block" }}
    />
  );
}
