$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    $doc = $word.Documents.Open('C:\JARVIS2\Manual_Usuario_JARVIS.docx')

    # Reemplazar JARVIS 2.0 por JARVIS 4.0 si queda alguno
    $find = $doc.Content.Find
    $null = $find.Execute("JARVIS 2.0", $false, $false, $false, $false, $false, $true, 1, $false, "JARVIS 4.0", 2)

    # Buscar e insertar capacidades del escáner en sección 1 (si no estuviese ya)
    $seccion1_encontrada = $false
    foreach ($p in $doc.Paragraphs) {
        if ($p.Range.Text -like "*Lectura y An*lisis de Documentos*" -and $p.Range.Text -notlike "*Escaneo de Documentos*") {
            # Insertar un nuevo párrafo después de este
            $range = $p.Range
            $range.Collapse(0) # Collapse to End
            $range.Text = "`nEscaneo de Documentos: Capacidad para digitalizar hojas de forma interactiva usando tu escáner físico, compilar múltiples páginas en un único PDF y abrirlo automáticamente en Acrobat Pro."
            $seccion1_encontrada = $true
            break
        }
    }

    # Insertar capacidades nuevas de JARVIS 4.0 (DLCs, Búsqueda AND, Gemini 3.5, Chat Limpio)
    # Buscaremos la sección de Memoria a largo plazo o Escaneo de Documentos para meter las novedades
    $novedades_insertadas = $false
    foreach ($p in $doc.Paragraphs) {
        if ($p.Range.Text -like "*Memoria a largo plazo*" -and $p.Range.Text -notlike "*Búsqueda local multi-palabra*") {
            $range = $p.Range
            $range.Collapse(0) # Collapse to End
            $range.Text = "`nBúsqueda local multi-palabra (AND): El buscador de archivos (`Buscar-Archivo.ps1`) ahora permite buscar términos en cualquier orden (ej: 'control compras' encontrará 'Control de compras')." +
                          "`nPersistencia real de DLCs: Los interruptores de Memoria Vectorial, Clicky (Visión) y YouTube en el panel lateral se guardan permanentemente en config.yaml." +
                          "`nEnrutamiento Híbrido (MoE): Jarvis conmuta automáticamente al cerebro de la nube (usando gemini-3.5-flash) para tareas complejas o lectura visual, optimizando cuotas y rapidez." +
                          "`nMensajería Limpia: Cuando 'Mostrar Pensamiento' está desactivado, el chat oculta el código técnico y los razonamientos intermedios, ofreciendo una conversación limpia."
            $novedades_insertadas = $true
            break
        }
    }

    # Buscar e insertar ejemplos nuevos en sección 2
    $ejemplos_nuevos_insertados = $false
    foreach ($p in $doc.Paragraphs) {
        if ($p.Range.Text -like "*Escaneo inteligente*" -and $p.Range.Text -notlike "*Busca la carpeta compras de control*") {
            $range = $p.Range
            $range.Collapse(0) # Collapse to End
            $range.Text = "`nBúsqueda inteligente AND: `"Jarvis, busca la carpeta compras de control`"." +
                          "`nCharla silenciosa: Desactiva 'Mostrar Pensamiento' para una interacción directa y limpia."
            $ejemplos_nuevos_insertados = $true
            break
        }
    }

    $doc.Save()
    $doc.SaveAs('C:\JARVIS2\Manual_Usuario_JARVIS.pdf', 17) # wdFormatPDF
    Write-Host "Manual de Usuario (DOCX y PDF) actualizado con éxito en C:\JARVIS2."
} catch {
    Write-Error $_
} finally {
    if ($doc) { $doc.Close() }
    $word.Quit()
}
