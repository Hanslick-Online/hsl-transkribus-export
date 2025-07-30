#!/bin/bash
# Script to patch page2tei-0.xsl for orphaned TextLines

python3 << 'EOF'
import re
import sys
import os

def patch_xsl():
    """Apply patches to page2tei-0.xsl"""
    
    # Change to page2tei directory
    os.chdir('page2tei')
    
    # Create backup
    if not os.path.exists('page2tei-0.xsl.backup'):
        with open('page2tei-0.xsl', 'r') as src, open('page2tei-0.xsl.backup', 'w') as dst:
            dst.write(src.read())
    
    # Read the original file
    with open('page2tei-0.xsl.backup', 'r') as f:
        content = f.read()
    
    # First patch: Add orphaned TextLine handling to facsimile mode
    # Look for the specific Page template in facsimile mode
    facsimile_pattern = r'(<xsl:apply-templates\s+select="p:PrintSpace \| p:TextRegion.*?mode="facsimile"/>\s*\n)(\s*<xsl:text>)'
    facsimile_replacement = r'''\1         
         <!-- Process orphaned TextLines for facsimile -->
         <xsl:variable name="orphaned-textlines" select="p:TextLine[not(parent::p:TextRegion)] | pc:TextLine[not(parent::pc:TextRegion)]"/>
         <xsl:if test="$orphaned-textlines">
            <!-- Create a zone for orphaned lines -->
            <zone xml:id="facs_{$numCurr}_orphaned" rendition="Orphaned">
               <xsl:apply-templates select="$orphaned-textlines" mode="facsimile"/>
            </zone>
         </xsl:if>
\2'''
    
    # Apply facsimile patch
    content = re.sub(facsimile_pattern, facsimile_replacement, content, flags=re.DOTALL)
    
    # Second patch: Add orphaned TextLine handling to text mode
    # Look for the end of the Page template in text mode
    lines = content.split('\n')
    in_page_text_template = False
    patched = False
    
    for i, line in enumerate(lines):
        if 'template match="p:Page | pc:Page" mode="text"' in line:
            in_page_text_template = True
        elif in_page_text_template and '</xsl:template>' in line and not patched:
            # Insert before the closing </xsl:template>
            lines.insert(i, '      ')
            lines.insert(i+1, '      <!-- Process orphaned TextLines that are direct children of Page (not in any TextRegion) -->')
            lines.insert(i+2, '      <xsl:variable name="orphaned-textlines" select="p:TextLine[not(parent::p:TextRegion)] | pc:TextLine[not(parent::pc:TextRegion)]"/>')
            lines.insert(i+3, '      <xsl:if test="$orphaned-textlines">')
            lines.insert(i+4, '         <ab type="orphaned-lines" facs="#facs_{$numCurr}_orphaned">')
            lines.insert(i+5, '            <xsl:apply-templates select="$orphaned-textlines"/>')
            lines.insert(i+6, '         </ab>')
            lines.insert(i+7, '      </xsl:if>')
            patched = True
            break
    
    content = '\n'.join(lines)
    
    # Write the patched file
    with open('page2tei-0.xsl', 'w') as f:
        f.write(content)
    
    # Change back
    os.chdir('..')
    print("page2tei-0.xsl patched successfully")

if __name__ == '__main__':
    patch_xsl()
EOF
