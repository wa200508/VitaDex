# Printing a VitaDex card

Open a saved card in **My Card Book**, select **Export for printing**, and choose Letter
or A4. Android opens its system Save dialog; desktop saves a PDF under the app's private
`exports` directory and displays the path. No upload or print order is placed.

The PDF contains:

1. A front with the selected private artwork, common/scientific name and status.
2. A back with a short description, revision and status.
3. Full fact and reference pages, continuing onto more pages when needed.

Front and back are centered on matching sheets. Trim is 2.5 x 3.5 inches with 0.125-inch
background bleed and crop marks. Print at **actual size / 100%**, using long-edge duplex
on portrait sheets for an initial proof. Print only pages 1-2 on card stock; print the
reference appendix separately. Test alignment on ordinary paper before ordering copies.
Confirm stock, color and bleed requirements with the print provider; this is an RGB PDF
proof, not a claim of universal press-ready/PDF-X compatibility.

Fonts are embedded (DejaVu, with bundled license). Original/artwork aspect ratio is
preserved, no photos are fetched, and missing or low-resolution art is reported. Unsupported
font characters or a title that cannot fit fail explicitly instead of silently dropping
text. Draft and suggested-identification labels remain visible in the PDF.

Export uses a background worker and a snapshot of the saved card. A failed generation
cannot replace an existing PDF. On Android, canceling Save removes the temporary PDF;
failed writes may leave an empty/partial document at the selected provider destination,
which the user can remove in Files. No broad storage permission is requested.

Current limits: one card per export, no PDF preview within VitaDex, no multi-card sheet
layout, no CMYK conversion, and no automatic printing. Complex-script shaping and fonts
for every writing system remain future work. Validate Android saving and a physical
print proof on target devices before treating this as production-ready.
