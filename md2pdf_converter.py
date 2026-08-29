from markdown_pdf import MarkdownPdf, Section

pdf = MarkdownPdf(toc_level=2)
pdf.add_section(Section(open("ACADEMIQ_COMPREHENSIVE_SUMMARY.md").read()))
pdf.save("ACADEMIQ_COMPREHENSIVE_SUMMARY.pdf")
print("PDF generated successfully.")
