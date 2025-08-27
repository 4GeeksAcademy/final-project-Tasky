import React, { useState } from "react";
import "../index.css"; 


const sampleOffers = [
  { id: 1, title: "Oferta 1", description: "Descripción de la oferta 1", price: 500 },
  { id: 2, title: "Oferta 2", description: "Descripción de la oferta 2", price: 750 },
  { id: 3, title: "Oferta 3", description: "Descripción de la oferta 3", price: 1200 },
  { id: 4, title: "Oferta 4", description: "Descripción de la oferta 4", price: 900 },
];

export const MyOffers = () => {
  const [offers] = useState(sampleOffers);
  const [activeOffer, setActiveOffer] = useState(null);

  const handleOpenModal = (offer) => setActiveOffer(offer);
  const handleCloseModal = () => setActiveOffer(null);

  return (
    <div className="container mt-5 text-center">
      <h2>Tasky Offers</h2>

      <div className="offers-container mt-4">
        {offers.map((offer) => (
          <div key={offer.id} className="offer-card p-4 border rounded shadow-sm">
            <h4>{offer.title}</h4>
            <p>{offer.description}</p>
            <p className="text-success">${offer.price}</p>
            <button className="btn btn-primary" onClick={() => handleOpenModal(offer)}>
              Ver detalles
            </button>
          </div>
        ))}
      </div>

      {activeOffer && (
        <div className="modal-backdrop">
          <div className="modal-content p-4">
            <h4>{activeOffer.title}</h4>
            <p>{activeOffer.description}</p>
            <p className="text-success">${activeOffer.price}</p>
            <div className="d-flex justify-content-between mt-3">
              <button className="btn btn-success" onClick={handleCloseModal}>
                Aceptar
              </button>
              <button className="btn btn-danger" onClick={handleCloseModal}>
                Rechazar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MyOffers