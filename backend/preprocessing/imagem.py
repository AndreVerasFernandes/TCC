"""
Pré-processamento de imagens com OpenCV.
Funções auxiliares para tratar imagens antes de enviar à IA.

TODO: ajustar parâmetros (dimensões, filtros) conforme necessidade do modelo.
"""

import cv2
import numpy as np


def redimensionar(imagem_bytes: bytes, largura: int = 640, altura: int = 640) -> bytes:
    """
    Redimensiona a imagem para as dimensões esperadas pelo modelo de IA.

    Parâmetros:
        imagem_bytes: conteúdo da imagem em bytes
        largura: largura alvo em pixels
        altura: altura alvo em pixels

    Retorna:
        Imagem redimensionada em bytes (JPEG).
    """
    arr = np.frombuffer(imagem_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("Não foi possível decodificar a imagem.")

    img_redimensionada = cv2.resize(img, (largura, altura), interpolation=cv2.INTER_AREA)
    _, buffer = cv2.imencode(".jpg", img_redimensionada)
    return buffer.tobytes()


def normalizar_iluminacao(imagem_bytes: bytes) -> bytes:
    """
    Aplica equalização de histograma no canal de luminância (YCrCb)
    para normalizar diferenças de iluminação entre capturas.

    Parâmetros:
        imagem_bytes: conteúdo da imagem em bytes

    Retorna:
        Imagem normalizada em bytes (JPEG).
    """
    arr = np.frombuffer(imagem_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("Não foi possível decodificar a imagem.")

    # Converte para YCrCb e equaliza o canal Y (luminância)
    ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    ycrcb[:, :, 0] = cv2.equalizeHist(ycrcb[:, :, 0])
    img_normalizada = cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)

    _, buffer = cv2.imencode(".jpg", img_normalizada)
    return buffer.tobytes()


def remover_ruido(imagem_bytes: bytes) -> bytes:
    """
    Aplica filtro bilateral para remover ruído preservando bordas.
    Útil para imagens capturadas em ambientes hospitalares com iluminação artificial.

    Parâmetros:
        imagem_bytes: conteúdo da imagem em bytes

    Retorna:
        Imagem filtrada em bytes (JPEG).
    """
    arr = np.frombuffer(imagem_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("Não foi possível decodificar a imagem.")

    img_limpa = cv2.bilateralFilter(img, d=9, sigmaColor=75, sigmaSpace=75)

    _, buffer = cv2.imencode(".jpg", img_limpa)
    return buffer.tobytes()
