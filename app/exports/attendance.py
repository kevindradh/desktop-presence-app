"""XLSX/PDF exports of the exact loaded report; publish only complete files."""
from dataclasses import dataclass
from datetime import date,datetime
from html import escape
import os
from pathlib import Path
from tempfile import mkstemp
from threading import Lock
from zoneinfo import ZoneInfo

from app.services.attendance import EVENTS
from app.services.database import DataValidationError
from app.services.reports import STATUS

HEADERS=('Tanggal kerja','ID anggota','Nama','Grup','Shift','Status','Masuk','Keluar',
         'Mulai istirahat','Selesai istirahat','Pulang awal','Sumber OUT','Perangkat')
FONT_LOCK=Lock()


def stamp(value,zone):
    return value.astimezone(ZoneInfo(zone)).strftime('%d/%m/%Y %H:%M:%S') if value else ''


def display_row(row,zone):
    return (row.work_date.strftime('%d/%m/%Y'),row.code,row.name,row.group,row.shift,STATUS[row.status],
        stamp(row.check_in,zone),stamp(row.check_out,zone),
        '; '.join(stamp(value,zone) for value in row.break_out),'; '.join(stamp(value,zone) for value in row.break_in),
        'Ya' if row.early else ('Tidak' if row.check_out else ''),
        'Otomatis' if row.automatic else ('Scan' if row.check_out else ''),row.devices)


def metadata(snapshot):
    f=snapshot.filters
    status='Hadir (termasuk terlambat)' if f.status=='ATTENDED' else STATUS.get(f.status,'Semua status')
    return (f'Periode {f.start:%d/%m/%Y} sampai {f.end:%d/%m/%Y}. Tanggal kerja mengikuti awal shift.',
            f'Grup: {snapshot.group_label}. Shift: {snapshot.shift_label}. Anggota: {f.member or "Semua"}. Status: {status}.',
            f'Dimuat {stamp(snapshot.created,snapshot.zone)} ({snapshot.zone}). {len(snapshot.rows)} baris. Semua halaman hasil filter.',
            'Hadir mencakup Terlambat; Izin/Absent/Belum masuk berasal dari jadwal aktif dan kalender LOCAL saat dimuat.')


def write_xlsx(snapshot,path,context):
    import math
    import unicodedata
    import pandas as pd
    from openpyxl.styles import Alignment,Font,PatternFill
    from openpyxl.worksheet.table import Table,TableStyleInfo
    zone=ZoneInfo(snapshot.zone)
    def local(value):return value.astimezone(zone).replace(tzinfo=None) if value else None
    values=[]
    for i,row in enumerate(snapshot.rows):
        if i%250==0:context.checkpoint()
        result=list(display_row(row,snapshot.zone))
        result[0],result[6],result[7]=row.work_date,local(row.check_in),local(row.check_out)
        values.append(result)
    details=[(e.work_date,e.code,e.name,EVENTS[e.event],local(e.timestamp),e.device,'Otomatis' if e.automatic else 'Scan') for e in snapshot.events]
    with pd.ExcelWriter(path,engine='openpyxl',date_format='DD/MM/YYYY',datetime_format='DD/MM/YYYY HH:MM:SS') as writer:
        for name,headers,rows in (('Kehadiran',HEADERS,values),('Detail event',('Tanggal kerja','ID anggota','Nama','Aktivitas','Waktu','Perangkat','Sumber'),details)):
            context.checkpoint()
            pd.DataFrame(rows,columns=headers).to_excel(writer,index=False,sheet_name=name,startrow=7)
            sheet=writer.sheets[name]
            sheet.sheet_view.showGridLines=False
            sheet.merge_cells(start_row=1,start_column=1,end_row=1,end_column=len(headers))
            sheet.cell(1,1,'StarGate - Laporan Kehadiran').font=Font(name='Arial',size=16,bold=True,color='213E31')
            sheet.row_dimensions[1].height=32
            for i,text in enumerate(metadata(snapshot),3):
                sheet.merge_cells(start_row=i,start_column=1,end_row=i,end_column=len(headers))
                sheet.cell(i,1,text).alignment=Alignment(wrap_text=True,vertical='center')
                sheet.cell(i,1).font=Font(name='Arial',size=10,color='60736B')
                capacity=323 if name=='Kehadiran' else 151
                sheet.row_dimensions[i].height=max(30,math.ceil(len(text)/capacity)*15+8)
            widths=(15,20,34,24,24,23,23,23,35,35,15,16,28) if name=='Kehadiran' else (15,20,34,24,24,28,16)
            from openpyxl.utils import get_column_letter
            for i,width in enumerate(widths,1):sheet.column_dimensions[get_column_letter(i)].width=width
            for cell in sheet[8]:
                cell.font=Font(name='Arial',size=11,bold=True,color='FFFFFF');cell.fill=PatternFill('solid',fgColor='2D6240')
                cell.alignment=Alignment(wrap_text=True,vertical='center',horizontal='center')
            sheet.row_dimensions[8].height=30
            for row in sheet.iter_rows(min_row=9):
                lines=1
                for i,cell in enumerate(row):
                    # User-controlled text is literal, including leading '='.
                    if isinstance(cell.value,str):cell.data_type='s'
                    cell.font=Font(name='Arial',size=11,color='243A33')
                    cell.alignment=Alignment(wrap_text=True,vertical='top',horizontal='left',indent=1)
                    if isinstance(cell.value,datetime):cell.number_format='DD/MM/YYYY HH:MM:SS'
                    elif isinstance(cell.value,date):cell.number_format='DD/MM/YYYY'
                    if isinstance(cell.value,str):
                        wide=sum(2 if unicodedata.east_asian_width(char) in ('W','F') else 1 for char in cell.value)
                        lines=max(lines,math.ceil(wide/max(1,widths[i]-3))+cell.value.count('\n'))
                sheet.row_dimensions[row[0].row].height=min(409,max(32,lines*15+8))
            sheet.freeze_panes='D9'
            sheet.print_title_rows='1:8'
            sheet.sheet_properties.pageSetUpPr.fitToPage=True
            sheet.page_setup.orientation='landscape';sheet.page_setup.paperSize=sheet.PAPERSIZE_A3
            sheet.page_setup.fitToWidth=1;sheet.page_setup.fitToHeight=0
            if rows:
                table=Table(displayName='AttendanceSummary' if name=='Kehadiran' else 'AttendanceEvents',ref=f'A8:{get_column_letter(len(headers))}{sheet.max_row}')
                table.tableStyleInfo=TableStyleInfo(name='TableStyleMedium4',showRowStripes=True)
                sheet.add_table(table)
            else:sheet.cell(9,1,'Tidak ada data sesuai filter.')
            # Metadata also contains filter/name values and must stay literal.
            for row in sheet.iter_rows(min_row=1,max_row=7):
                for cell in row:
                    if isinstance(cell.value,str):cell.data_type='s'
            context.progress(70 if name=='Kehadiran' else 85)


def pdf_fonts():
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    import reportlab
    with FONT_LOCK:
        if 'StarGateVera' not in pdfmetrics.getRegisteredFontNames():
            directory=Path(reportlab.__file__).parent/'fonts'
            pdfmetrics.registerFont(TTFont('StarGateVera',str(directory/'Vera.ttf')))
            pdfmetrics.registerFont(TTFont('StarGateVeraBold',str(directory/'VeraBd.ttf')))
            pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))


def pdf_text(value):
    # Embed the ReportLab-bundled Vera Latin/Greek/Cyrillic font; standard CID
    # Japanese fallback for CJK rather than replacing names with black boxes.
    from reportlab.pdfbase import pdfmetrics
    cmap=pdfmetrics.getFont('StarGateVera').face.charToGlyph
    output=[]
    for char in str(value):
        if char in '\r\n':output.append('<br/>')
        elif ord(char) in cmap:output.append(escape(char))
        elif 0x3000<=ord(char)<=0x9fff or 0xff00<=ord(char)<=0xffef:
            output.append('<font name="HeiseiMin-W3">'+escape(char)+'</font>')
        else:
            raise DataValidationError('PDF belum mendukung salah satu karakter teks. Gunakan Excel agar teks lengkap tetap tersimpan.')
    return ''.join(output)


def write_pdf(snapshot,path,context):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4,landscape
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate,LongTable,Paragraph,Spacer,TableStyle
    pdf_fonts()
    text=ParagraphStyle('body',fontName='StarGateVera',fontSize=8.5,leading=12,wordWrap='CJK')
    heading=ParagraphStyle('heading',parent=text,fontName='StarGateVeraBold',fontSize=16,leading=21,textColor=colors.HexColor('#213e31'))
    header=ParagraphStyle('table_header',parent=text,textColor=colors.white,fontName='StarGateVeraBold')
    paragraph=lambda value:Paragraph(pdf_text(value),text)
    body=[Paragraph('StarGate - Laporan Kehadiran',heading),Spacer(1,10)]
    body.extend(paragraph(line) for line in metadata(snapshot))
    body.append(Spacer(1,14))
    labels=('Tanggal / anggota','Grup / shift','Status','Masuk / keluar','Istirahat','Pulang / sumber / perangkat')
    data=[[Paragraph(label,header) for label in labels]]
    widths=[139,106,77,137,127,112]
    oversized=False
    for i,row in enumerate(snapshot.rows):
        if i%100==0:context.checkpoint()
        values=display_row(row,snapshot.zone)
        cells=(f'{values[0]}\n{row.code}\n{row.name}',f'{row.group}\n{row.shift}',values[5],
               f'Masuk: {values[6] or "-"}\nKeluar: {values[7] or "-"}',
               f'Mulai: {values[8] or "-"}\nSelesai: {values[9] or "-"}',
               f'Pulang awal: {values[10] or "-"}\nSumber OUT: {values[11] or "-"}\n{row.devices}')
        rendered=[paragraph(value) for value in cells]
        oversized=oversized or any(cell.wrap(width-14,10000)[1]>480 for cell,width in zip(rendered,widths))
        data.append(rendered)
    if not snapshot.rows:body.append(paragraph('Tidak ada data sesuai filter.'))
    else:
        table=LongTable(data,colWidths=widths,repeatRows=1,splitByRow=1,splitInRow=int(oversized),hAlign='LEFT')
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#2d6240')),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f1f5f0')]),
            ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
            ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),
            ('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor('#cbd9ce'))]))
        body.append(table)
    def page(canvas,doc):
        context.checkpoint()
        canvas.saveState();canvas.setFont('StarGateVera',8)
        canvas.setFillColor(colors.HexColor('#60736b'))
        canvas.drawString(28,20,'StarGate | '+snapshot.zone+' | '+f'{snapshot.filters.start} - {snapshot.filters.end}')
        canvas.drawRightString(landscape(A4)[0]-28,20,f'Halaman {doc.page}')
        canvas.restoreState()
    context.progress(65)
    SimpleDocTemplate(str(path),pagesize=landscape(A4),leftMargin=28,rightMargin=28,topMargin=28,bottomMargin=35,
        title='StarGate - Laporan Kehadiran',author='StarGate').build(body,onFirstPage=page,onLaterPages=page)
    context.checkpoint();context.progress(85)


@dataclass(frozen=True)
class ExportResult:
    path: str
    rows: int


def export_report(service,token,key,path,kind,context,*,overwrite=False):
    if kind not in ('xlsx','pdf'):raise DataValidationError('Format ekspor tidak didukung.')
    destination=Path(path).expanduser().absolute()
    if destination.suffix.lower()!='.'+kind:raise DataValidationError('Ekstensi file tidak sesuai format ekspor.')
    snapshot=service.snapshot(token,key)
    temporary=None
    try:
        context.checkpoint()
        if destination.exists() and not overwrite:raise DataValidationError('File sudah ada. Pilih nama lain atau konfirmasi penggantian.')
        descriptor,name=mkstemp(prefix='.stargate-report-',suffix='.'+kind,dir=destination.parent)
        os.close(descriptor);temporary=Path(name)
        (write_xlsx if kind=='xlsx' else write_pdf)(snapshot,temporary,context)
        context.checkpoint()
        def publish():
            def move():
                if overwrite:os.replace(temporary,destination)
                else:os.link(temporary,destination)
            context.commit(move)
        service.publish(token,key,publish)
        context.progress(100)
        return ExportResult(str(destination),len(snapshot.rows))
    except OSError:
        raise DataValidationError('File belum dapat disimpan. Periksa nama, izin folder, dan apakah file sedang dibuka.') from None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
