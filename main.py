import argparse
from detran import Detran

def main():
    parser = argparse.ArgumentParser(description='Detran Web Scraper')
    parser.add_argument('--capsolver_token', type=str, help='Capsolver token', required=True)
    parser.add_argument('--municipio', type=str, help='Municipio', default=None)
    parser.add_argument('--chassi', type=str, help='Chassi', default=None)
    parser.add_argument('--placa', type=str, help='Placa', default=None)
    args = parser.parse_args()

    print("\n\n")
    _detran = Detran()

    result = _detran.consulta_patio(
        capsolver_token=args.capsolver_token,
        municipio=args.municipio,
        chassi=args.chassi,
        placa=args.placa
    )

    print(f"\nResults: {result}")

if __name__ == "__main__":
    main()